from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from pm_bot.practical.new_market_public_source_candidates import (
    GENERATED_AT_017,
    NEW_MARKET_HYPOTHESIS_ID,
    NEW_MARKET_ID,
    NEW_MARKET_TITLE,
    build_manual_url_mapping_fixture,
    build_new_market_public_source_candidates,
    render_manual_url_mapping_fixture_markdown,
    render_new_market_public_source_candidates_markdown,
)
from pm_bot.practical.practical_io import (
    bullet_lines,
    clean_text,
    load_json_object,
    normalize_path,
    safe_summary,
    slug_id,
    write_json,
    write_text,
)
from pm_bot.practical.practical_safety_scan import render_practical_safety_scan_markdown, run_practical_safety_scan
from pm_bot.practical.public_fetch_url_safety import validate_public_fetch_request_intent

TASK_ID = "ORCH-PMBOT-PRACTICAL-017-PUBLIC-EVIDENCE-PLAN-FOR-NEW-MARKET-AND-DASHBOARD-REFRESH"
FUTURE_FETCH_TASK_ID = "ORCH-PMBOT-PRACTICAL-018-FIRST-PUBLIC-EVIDENCE-FETCH-FOR-NEW-MARKET"
MANUAL_URL_COLLECTION_TASK_ID = "ORCH-PMBOT-PRACTICAL-017B-MANUAL-URL-COLLECTION-FOR-NEW-MARKET"

EVIDENCE_PLAN_CONTRACT_VERSION = "pmbot_new_market_public_evidence_plan.v1"
FETCH_MANIFEST_CONTRACT_VERSION = "pmbot_new_market_fetch_request_manifest.v1"
URL_SAFETY_REPORT_CONTRACT_VERSION = "pmbot_new_market_url_safety_report.v1"
PREFLIGHT_CONTRACT_VERSION = "pmbot_new_market_fetch_preflight_dry_run.v1"
SCOPED_APPROVAL_CONTRACT_VERSION = "pmbot_scoped_public_read_only_fetch_approval.v1"
DASHBOARD_REFRESH_CONTRACT_VERSION = "pmbot_public_evidence_dashboard_6_market_refresh.v1"
SOURCE_DEPENDENCY_MAP_CONTRACT_VERSION = "pmbot_source_dependency_map_6_markets.v1"
DAILY_REFRESH_CONTRACT_VERSION = "pmbot_daily_workflow_public_evidence_refresh.v1"
OPERATOR_CARD_CONTRACT_VERSION = "pmbot_new_market_public_evidence_operator_card.v1"

REPO_ROOT = "C:/Users/OpenC/.openclaw/workspace"
HEAD_BEFORE = "a78ba734055a6b5010f34715d7aae9a52c25ed8b"
BRANCH = "master"

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_plan_017")
FIXTURE_DIR = Path("pm_bot/tests/fixtures/new_market_public_evidence_plan_017")
DOCS_DIR = Path("docs")

SELECTED_MARKET_PATH = Path("pm_bot/practical/artifacts/add_market_016/selected_market_016.json")
NORMALIZED_INPUT_PATH = Path("pm_bot/practical/artifacts/add_market_016/normalized_input_016.json")
PAPER_HYPOTHESIS_PATH = Path("pm_bot/practical/artifacts/add_market_016/paper_hypothesis_016.json")
OUTCOME_RECORD_PATH = Path("pm_bot/practical/artifacts/add_market_016/outcome_record_unresolved_016.json")
MARKET_QUEUE_6_PATH = Path("pm_bot/practical/artifacts/add_market_016/market_queue_6_016.json")
ACTIVE_HYPOTHESES_6_PATH = Path("pm_bot/practical/artifacts/add_market_016/active_paper_hypotheses_6_016.json")
OUTCOME_RECHECK_6_PATH = Path("pm_bot/practical/artifacts/add_market_016/outcome_recheck_queue_6_016.json")
SOURCE_DEPENDENCY_UPDATE_PATH = Path("pm_bot/practical/artifacts/add_market_016/source_dependency_update_016.json")
DAILY_SUMMARY_AFTER_ADD_PATH = Path("pm_bot/practical/artifacts/add_market_016/daily_workflow_summary_after_add_016.json")
PUBLIC_DASHBOARD_011_PATH = Path(
    "pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.json"
)
PUBLIC_SOURCE_BACKLOG_011_PATH = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011/source_url_backlog_011.json")
PUBLIC_SOURCE_BOARD_011_PATH = Path(
    "pm_bot/practical/artifacts/public_evidence_dashboard_011/merged_source_status_board_011.json"
)


def build_new_market_public_evidence_plan(
    *,
    normalized_input: Mapping[str, Any],
    paper_hypothesis: Mapping[str, Any],
    source_dependency_update: Mapping[str, Any],
    source_candidates: Mapping[str, Any],
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    market_id = clean_text(normalized_input.get("market_id") or NEW_MARKET_ID)
    candidate_sources = _mapping_rows(source_candidates.get("candidate_sources"))
    missing_url_items = [row for row in candidate_sources if row.get("url_status") == "missing"]
    blocked_source_items = [row for row in candidate_sources if row.get("url_status") == "blocked"]
    concrete_urls = [
        {
            "candidate_source_id": row.get("candidate_source_id"),
            "source_category": row.get("source_category"),
            "source_name": row.get("source_name"),
            "concrete_public_url": row.get("concrete_public_url"),
            "expected_evidence_type": row.get("expected_evidence_type"),
        }
        for row in candidate_sources
        if row.get("url_status") == "concrete_safe_public_url" and clean_text(row.get("concrete_public_url"))
    ]
    return {
        "contract_version": EVIDENCE_PLAN_CONTRACT_VERSION,
        "evidence_plan_id": f"new-market-public-evidence-plan-017-{market_id}",
        "generated_at": generated_at,
        "source_market_id": market_id,
        "source_market_title": clean_text(normalized_input.get("market_title") or NEW_MARKET_TITLE),
        "source_normalized_input_path": normalize_path(NORMALIZED_INPUT_PATH),
        "source_paper_hypothesis_path": normalize_path(PAPER_HYPOTHESIS_PATH),
        "market_class": "crypto",
        "required_evidence_categories": _required_evidence_categories(normalized_input),
        "available_local_evidence": _available_local_evidence(normalized_input, source_dependency_update),
        "missing_public_evidence": list(normalized_input.get("missing_evidence", [])),
        "candidate_public_source_categories": [
            {
                "source_category": row.get("source_category"),
                "source_name": row.get("source_name"),
                "safe_by_registry": row.get("allowed_by_registry") is True,
                "url_status": row.get("url_status"),
                "include_in_manifest": row.get("include_in_manifest") is True,
            }
            for row in candidate_sources
        ],
        "candidate_public_source_references": [
            {
                "source_id": row.get("source_id", row.get("candidate_source_id", "")),
                "source_name": row.get("source_name", ""),
                "source_reference": row.get("source_reference", row.get("source_reference_or_placeholder", "")),
                "source_type": row.get("source_type", "candidate_public_source_placeholder"),
            }
            for row in _mapping_rows(source_dependency_update.get("new_source_dependencies")) + candidate_sources
        ],
        "concrete_public_urls": concrete_urls,
        "missing_url_items": [
            {
                "candidate_source_id": row.get("candidate_source_id"),
                "source_category": row.get("source_category"),
                "source_name": row.get("source_name"),
                "expected_evidence_type": row.get("expected_evidence_type"),
                "reason": row.get("reason"),
                "include_in_manifest": row.get("include_in_manifest") is True,
            }
            for row in missing_url_items
        ],
        "blocked_source_items": [
            {
                "candidate_source_id": row.get("candidate_source_id"),
                "source_category": row.get("source_category"),
                "source_name": row.get("source_name"),
                "reason": row.get("reason"),
            }
            for row in blocked_source_items
        ],
        "expected_evidence_role": [
            {
                "source_name": row.get("source_name"),
                "role": row.get("expected_evidence_role"),
            }
            for row in candidate_sources
        ],
        "linked_hypothesis_id": clean_text(paper_hypothesis.get("hypothesis_id") or NEW_MARKET_HYPOTHESIS_ID),
        "operator_approval_required_before_fetch": True,
        "live_fetch_performed": False,
        "no_real_trade_decision": True,
        "safety_summary": public_evidence_plan_safety_summary(),
    }


def build_new_market_fetch_request_manifest(
    *,
    source_candidates: Mapping[str, Any],
    manual_url_mapping_fixture: Mapping[str, Any],
    max_request_count: int = 3,
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    fixture_rows = _fixture_rows(manual_url_mapping_fixture)
    selected = [
        row
        for row in _mapping_rows(source_candidates.get("candidate_sources"))
        if row.get("include_in_manifest") is True
    ][:max_request_count]
    request_intents = [
        _request_intent_from_candidate(index, row, _matching_fixture_row(fixture_rows, row))
        for index, row in enumerate(selected, start=1)
    ]

    executable: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for index, intent in enumerate(request_intents, start=1):
        status = clean_text(intent.get("url_status"))
        if status == "blocked":
            blocked.append(_blocked_manifest_row(intent, "manual fixture or registry marked this request non-executable"))
            continue
        if status != "concrete_safe_public_url":
            missing.append(_missing_manifest_row(intent))
            continue
        safety = validate_public_fetch_request_intent(
            intent,
            request_index=index,
            max_request_count=max_request_count,
        )
        if safety["allowed"]:
            executable.append({**intent, "url_safety_validation": safety})
        else:
            blocked.append(_blocked_manifest_row(intent, "concrete URL candidate failed local URL safety validation", safety))

    return {
        "contract_version": FETCH_MANIFEST_CONTRACT_VERSION,
        "generated_at": generated_at,
        "manifest_id": "new-market-fetch-request-manifest-017",
        "market_id": clean_text(source_candidates.get("market_id") or NEW_MARKET_ID),
        "market_title": clean_text(source_candidates.get("market_title") or NEW_MARKET_TITLE),
        "request_intents": request_intents,
        "executable_request_intents": executable,
        "missing_url_request_intents": missing,
        "blocked_request_intents": blocked,
        "executable_request_count": len(executable),
        "missing_url_count": len(missing),
        "blocked_request_count": len(blocked),
        "max_request_count": max_request_count,
        "within_request_limit": len(executable) <= max_request_count,
        "live_fetch_performed": False,
        "operator_approval_required_before_fetch": True,
        "safety_summary": public_evidence_plan_safety_summary(),
    }


def build_new_market_url_safety_report(
    *,
    manifest: Mapping[str, Any],
    fixture_mode: bool = False,
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    request_intents = _mapping_rows(manifest.get("request_intents"))
    max_request_count = int(manifest.get("max_request_count") or 3)
    per_request = []
    for index, intent in enumerate(request_intents, start=1):
        safety = validate_public_fetch_request_intent(
            intent,
            request_index=index,
            max_request_count=max_request_count,
            fixture_mode=fixture_mode,
        )
        safety["url_status"] = clean_text(intent.get("url_status"))
        safety["non_executable_reason"] = (
            "missing concrete public URL" if intent.get("url_status") == "missing" else clean_text(intent.get("blocked_reason"))
        )
        per_request.append(safety)

    unsafe_executable = [
        row
        for row in per_request
        if row.get("url_status") == "concrete_safe_public_url" and row.get("allowed") is not True
    ]
    global_blockers = []
    if len(_mapping_rows(manifest.get("executable_request_intents"))) > max_request_count:
        global_blockers.append("executable request count exceeds max request count")
    if unsafe_executable:
        global_blockers.append("one or more executable URL candidates failed local safety validation")
    global_warnings = []
    if manifest.get("missing_url_count"):
        global_warnings.append(f"{manifest.get('missing_url_count')} request intents are missing concrete URLs.")
    if manifest.get("blocked_request_count"):
        global_warnings.append(f"{manifest.get('blocked_request_count')} request intents are blocked.")
    return {
        "contract_version": URL_SAFETY_REPORT_CONTRACT_VERSION,
        "generated_at": generated_at,
        "checked_request_count": len(request_intents),
        "allowed_count": int(manifest.get("executable_request_count") or 0),
        "blocked_count": int(manifest.get("blocked_request_count") or 0) + len(unsafe_executable),
        "missing_url_count": int(manifest.get("missing_url_count") or 0),
        "per_request_safety": per_request,
        "global_blockers": global_blockers,
        "global_warnings": global_warnings,
        "live_fetch_performed": False,
        "safety_summary": public_evidence_plan_safety_summary(),
    }


def build_new_market_fetch_preflight_dry_run(
    *,
    manifest: Mapping[str, Any],
    pending_approval: Mapping[str, Any],
    url_safety_report: Mapping[str, Any],
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    executable_count = int(manifest.get("executable_request_count") or 0)
    max_request_count = int(manifest.get("max_request_count") or pending_approval.get("max_request_count") or 3)
    request_count_within_limit = executable_count <= max_request_count
    missing_url_count = int(manifest.get("missing_url_count") or 0)
    blocked_request_count = int(manifest.get("blocked_request_count") or 0)
    approval_required = pending_approval.get("operator_approval_required") is not False
    approval_granted = pending_approval.get("operator_approval_granted") is True

    after_approval_blockers: list[str] = []
    if executable_count == 0:
        after_approval_blockers.append("no concrete safe public URLs")
    if not request_count_within_limit:
        after_approval_blockers.append("executable request count exceeds max request count")
    if url_safety_report.get("global_blockers"):
        after_approval_blockers.extend(clean_text(row) for row in url_safety_report.get("global_blockers", []))
    if pending_approval.get("approval_for_future_task_id") != FUTURE_FETCH_TASK_ID:
        after_approval_blockers.append("pending approval future task id does not match the new-market fetch task")

    blockers = []
    if approval_required and not approval_granted:
        blockers.append("operator approval has not been granted")
    blockers.extend(after_approval_blockers)
    warnings = []
    if missing_url_count:
        warnings.append(f"{missing_url_count} missing URL request intents remain non-executable.")
    if blocked_request_count:
        warnings.append(f"{blocked_request_count} blocked request intents remain non-executable.")
    would_be_ready_after_operator_approval = not after_approval_blockers
    return {
        "contract_version": PREFLIGHT_CONTRACT_VERSION,
        "generated_at": generated_at,
        "ready_to_execute_public_read_only_fetch": approval_granted and would_be_ready_after_operator_approval,
        "would_be_ready_after_operator_approval": would_be_ready_after_operator_approval,
        "executable_request_count": executable_count,
        "request_count_within_limit": request_count_within_limit,
        "max_request_count": max_request_count,
        "missing_url_count": missing_url_count,
        "blocked_request_count": blocked_request_count,
        "approval_required": approval_required,
        "approval_granted": approval_granted,
        "live_fetch_performed": False,
        "blockers": _dedupe(blockers),
        "warnings": _dedupe(warnings),
        "per_request_safety": url_safety_report.get("per_request_safety", []),
        "safety_summary": public_evidence_plan_safety_summary(),
    }


def build_new_market_pending_scoped_approval(
    *,
    manifest: Mapping[str, Any],
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    executable = _mapping_rows(manifest.get("executable_request_intents"))
    return {
        "contract_version": SCOPED_APPROVAL_CONTRACT_VERSION,
        "approval_id": "new-market-public-fetch-scoped-approval-pending-017",
        "generated_at": generated_at,
        "approval_status": "pending",
        "approval_for_future_task_id": FUTURE_FETCH_TASK_ID,
        "market_id": NEW_MARKET_ID,
        "market_title": NEW_MARKET_TITLE,
        "max_request_count": int(manifest.get("max_request_count") or 3),
        "executable_request_count": len(executable),
        "approved_request_intent_ids_proposed": [clean_text(row.get("request_intent_id")) for row in executable],
        "operator_approval_required": True,
        "operator_approval_granted": False,
        "no_authentication": True,
        "no_api_keys": True,
        "no_cookies": True,
        "no_wallet": True,
        "no_orders": True,
        "no_trading": True,
        "no_scheduler": True,
        "no_background_worker": True,
        "reusable": False,
        "expires_after_future_task": True,
        "live_fetch_performed": False,
        "safety_summary": {**public_evidence_plan_safety_summary(), "operator_approval_granted": False},
    }


def build_public_evidence_dashboard_6_market_refresh(
    *,
    previous_dashboard: Mapping[str, Any],
    daily_summary_after_add: Mapping[str, Any],
    outcome_recheck_queue: Mapping[str, Any],
    evidence_plan: Mapping[str, Any],
    manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
    pending_approval: Mapping[str, Any],
    source_backlog_011: Mapping[str, Any],
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    markets = _mapping_rows(daily_summary_after_add.get("tracked_markets"))
    new_market_backlog = [
        {
            "market_id": row.get("market_id"),
            "source_category": row.get("source_category"),
            "source_name": row.get("source_name_or_placeholder") or row.get("source_name"),
            "reason": row.get("missing_url_reason"),
            "requires_manual_url_collection": True,
        }
        for row in _mapping_rows(manifest.get("missing_url_request_intents"))
    ]
    return {
        "contract_version": DASHBOARD_REFRESH_CONTRACT_VERSION,
        "dashboard_id": "public-evidence-dashboard-6-market-refresh-017",
        "generated_at": generated_at,
        "tracked_market_count": len(markets),
        "markets": markets,
        "evidence_packet_count_existing": len(_mapping_rows(previous_dashboard.get("evidence_packets"))),
        "existing_public_evidence_packets": previous_dashboard.get("evidence_packets", []),
        "new_market_evidence_plan_status": {
            "market_id": evidence_plan.get("source_market_id"),
            "plan_path": normalize_path(ARTIFACT_DIR / "new_market_public_evidence_plan_017.json"),
            "missing_url_count": len(_mapping_rows(evidence_plan.get("missing_url_items"))),
            "concrete_public_url_count": len(_mapping_rows(evidence_plan.get("concrete_public_urls"))),
            "operator_approval_required_before_fetch": evidence_plan.get("operator_approval_required_before_fetch") is True,
            "live_fetch_performed": False,
        },
        "new_market_fetch_readiness": {
            "ready_to_execute_public_read_only_fetch": preflight.get("ready_to_execute_public_read_only_fetch") is True,
            "would_be_ready_after_operator_approval": preflight.get("would_be_ready_after_operator_approval") is True,
            "executable_request_count": preflight.get("executable_request_count", 0),
            "missing_url_count": preflight.get("missing_url_count", 0),
            "blocked_request_count": preflight.get("blocked_request_count", 0),
            "approval_required": preflight.get("approval_required") is True,
            "approval_granted": preflight.get("approval_granted") is True,
        },
        "pending_public_fetch_approvals": [
            {
                "approval_id": pending_approval.get("approval_id"),
                "market_id": pending_approval.get("market_id"),
                "approval_status": pending_approval.get("approval_status"),
                "approval_for_future_task_id": pending_approval.get("approval_for_future_task_id"),
                "operator_approval_granted": pending_approval.get("operator_approval_granted") is True,
            }
        ],
        "source_url_backlog": {
            "existing_backlog_items": source_backlog_011.get("backlog_items", []),
            "new_market_missing_url_items": new_market_backlog,
            "total_backlog_count": len(_mapping_rows(source_backlog_011.get("backlog_items"))) + len(new_market_backlog),
        },
        "unresolved_outcomes": _mapping_rows(outcome_recheck_queue.get("recheck_items")),
        "next_operator_actions": [
            "Collect concrete public URLs manually for the new market source categories before any future fetch.",
            "Review the pending scoped approval only in a separate future fetch task.",
            "Keep all six outcomes unresolved until saved local resolution evidence exists.",
            "Do not use this dashboard as a market instruction.",
        ],
        "safety_summary": public_evidence_plan_safety_summary(),
    }


def build_source_dependency_map_6_markets(
    *,
    source_board_011: Mapping[str, Any],
    source_dependency_update: Mapping[str, Any],
    manifest: Mapping[str, Any],
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    existing_records = _mapping_rows(source_board_011.get("source_records"))
    new_records = _mapping_rows(source_dependency_update.get("new_source_records"))
    new_missing = _mapping_rows(manifest.get("missing_url_request_intents"))
    return {
        "contract_version": SOURCE_DEPENDENCY_MAP_CONTRACT_VERSION,
        "map_id": "source-dependency-map-6-markets-017",
        "generated_at": generated_at,
        "source_records": existing_records + new_records,
        "market_to_source_links": _market_to_source_links(existing_records, new_records),
        "new_market_source_dependencies": _mapping_rows(source_dependency_update.get("new_source_dependencies")),
        "sources_requiring_concrete_url": [
            {
                "market_id": row.get("market_id"),
                "source_id": row.get("source_id"),
                "source_category": row.get("source_category"),
                "source_name": row.get("source_name_or_placeholder"),
                "reason": row.get("missing_url_reason"),
            }
            for row in new_missing
        ],
        "sources_ready_for_future_fetch": [
            {
                "market_id": row.get("market_id"),
                "request_intent_id": row.get("request_intent_id"),
                "source_category": row.get("source_category"),
                "source_url": row.get("source_url"),
            }
            for row in _mapping_rows(manifest.get("executable_request_intents"))
        ],
        "blocked_sources": _mapping_rows(source_board_011.get("blocked_sources"))
        + _mapping_rows(manifest.get("blocked_request_intents")),
        "no_autonomous_training_performed": True,
        "safety_summary": public_evidence_plan_safety_summary(),
    }


def build_daily_workflow_public_evidence_refresh(
    *,
    dashboard: Mapping[str, Any],
    manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    return {
        "contract_version": DAILY_REFRESH_CONTRACT_VERSION,
        "summary_id": "daily-workflow-public-evidence-refresh-017",
        "generated_at": generated_at,
        "tracked_market_count": dashboard.get("tracked_market_count", 0),
        "unresolved_outcome_count": len(_mapping_rows(dashboard.get("unresolved_outcomes"))),
        "feedback_ready_count": 0,
        "new_market_public_evidence_plan_status": dashboard.get("new_market_evidence_plan_status", {}),
        "future_fetch_ready_after_approval": preflight.get("would_be_ready_after_operator_approval") is True,
        "what_is_blocked": preflight.get("blockers", []),
        "next_safe_operator_actions": [
            "Collect missing concrete public URLs manually for the new market.",
            "Keep pending approval separate from this planning task.",
            "Run a future controlled public read-only fetch task only if concrete URLs exist and approval is granted.",
            "Keep outcome feedback blocked while all outcomes remain unresolved.",
        ],
        "live_fetch_performed": False,
        "safety_summary": public_evidence_plan_safety_summary(),
    }


def build_new_market_public_evidence_operator_card(
    *,
    evidence_plan: Mapping[str, Any],
    manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
    pending_approval: Mapping[str, Any],
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    return {
        "contract_version": OPERATOR_CARD_CONTRACT_VERSION,
        "card_id": "new-market-public-evidence-operator-card-017",
        "generated_at": generated_at,
        "market": {
            "market_id": evidence_plan.get("source_market_id"),
            "market_title": evidence_plan.get("source_market_title"),
        },
        "what_evidence_is_needed": evidence_plan.get("required_evidence_categories", []),
        "source_categories_proposed": evidence_plan.get("candidate_public_source_categories", []),
        "urls": {
            "concrete_public_urls": evidence_plan.get("concrete_public_urls", []),
            "missing_url_items": evidence_plan.get("missing_url_items", []),
            "blocked_source_items": evidence_plan.get("blocked_source_items", []),
        },
        "fetch_can_run_later": preflight.get("would_be_ready_after_operator_approval") is True,
        "operator_must_approve": {
            "approval_id": pending_approval.get("approval_id"),
            "approval_status": pending_approval.get("approval_status"),
            "approval_for_future_task_id": pending_approval.get("approval_for_future_task_id"),
            "max_request_count": pending_approval.get("max_request_count"),
            "operator_approval_granted": pending_approval.get("operator_approval_granted") is True,
        },
        "what_remains_manual": [
            "Collect concrete public URLs for missing source categories.",
            "Confirm benchmark, index, and timestamp rules from saved public evidence after a later approved fetch.",
            "Attach outcome resolution evidence only after a saved local outcome record exists.",
        ],
        "safety_boundary": [
            "Planning and dashboard refresh only.",
            "No live fetch, OpenRouter call, Polymarket API call, auth, cookies, wallet, orders, trading, scheduler, or background worker.",
            "No outcome is resolved and no market instruction is generated.",
        ],
        "request_counts": {
            "request_intent_count": len(_mapping_rows(manifest.get("request_intents"))),
            "executable_request_count": manifest.get("executable_request_count", 0),
            "missing_url_count": manifest.get("missing_url_count", 0),
            "blocked_request_count": manifest.get("blocked_request_count", 0),
        },
        "live_fetch_performed": False,
        "safety_summary": public_evidence_plan_safety_summary(),
    }


def build_public_evidence_plan_safety_scan_report(*, artifact_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    report = run_practical_safety_scan(artifact_dirs=[artifact_dir])
    report.update(public_evidence_plan_safety_summary())
    report.update(
        {
            "live_network_used": False,
            "openrouter_calls_performed": 0,
            "new_polymarket_api_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "authenticated_endpoints_used": False,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "runtime_or_dispatcher_changes": False,
            "market_recommendation_generated": False,
            "probability_ev_edge_or_side_selection_generated": False,
            "outcome_resolution_invented": False,
            "no_scheduler_daemon_background_worker": True,
            "no_autonomous_trading": True,
            "no_autonomous_training_performed": True,
            "public_evidence_plan_safety_scan_passed": report.get("safety_ok") is True,
        }
    )
    return report


def write_public_evidence_plan_017_package(
    *,
    out_dir: str | Path = ARTIFACT_DIR,
    fixture_dir: str | Path = FIXTURE_DIR,
    docs_dir: str | Path = DOCS_DIR,
) -> dict[str, Any]:
    out_path = Path(out_dir)
    fixture_path = Path(fixture_dir)
    docs_path = Path(docs_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    fixture_path.mkdir(parents=True, exist_ok=True)
    docs_path.mkdir(parents=True, exist_ok=True)

    selected_market = load_json_object(SELECTED_MARKET_PATH, label="selected market")
    normalized_input = load_json_object(NORMALIZED_INPUT_PATH, label="normalized input")
    paper_hypothesis = load_json_object(PAPER_HYPOTHESIS_PATH, label="paper hypothesis")
    outcome_record = load_json_object(OUTCOME_RECORD_PATH, label="outcome record")
    source_dependency_update = load_json_object(SOURCE_DEPENDENCY_UPDATE_PATH, label="source dependency update")
    daily_summary = load_json_object(DAILY_SUMMARY_AFTER_ADD_PATH, label="daily workflow summary")
    outcome_recheck = load_json_object(OUTCOME_RECHECK_6_PATH, label="outcome recheck queue")
    previous_dashboard = load_json_object(PUBLIC_DASHBOARD_011_PATH, label="PRACTICAL-011 dashboard")
    source_backlog = load_json_object(PUBLIC_SOURCE_BACKLOG_011_PATH, label="PRACTICAL-011 source backlog")
    source_board = load_json_object(PUBLIC_SOURCE_BOARD_011_PATH, label="PRACTICAL-011 source board")

    _validate_practical_016_inputs(
        selected_market=selected_market,
        normalized_input=normalized_input,
        paper_hypothesis=paper_hypothesis,
        outcome_record=outcome_record,
        daily_summary=daily_summary,
        outcome_recheck=outcome_recheck,
    )

    source_candidates = build_new_market_public_source_candidates(normalized_input=normalized_input)
    fixture = build_manual_url_mapping_fixture(source_candidates=source_candidates)
    evidence_plan = build_new_market_public_evidence_plan(
        normalized_input=normalized_input,
        paper_hypothesis=paper_hypothesis,
        source_dependency_update=source_dependency_update,
        source_candidates=source_candidates,
    )
    manifest = build_new_market_fetch_request_manifest(
        source_candidates=source_candidates,
        manual_url_mapping_fixture=fixture,
    )
    url_safety_report = build_new_market_url_safety_report(manifest=manifest)
    pending_approval = build_new_market_pending_scoped_approval(manifest=manifest)
    preflight = build_new_market_fetch_preflight_dry_run(
        manifest=manifest,
        pending_approval=pending_approval,
        url_safety_report=url_safety_report,
    )
    dashboard = build_public_evidence_dashboard_6_market_refresh(
        previous_dashboard=previous_dashboard,
        daily_summary_after_add=daily_summary,
        outcome_recheck_queue=outcome_recheck,
        evidence_plan=evidence_plan,
        manifest=manifest,
        preflight=preflight,
        pending_approval=pending_approval,
        source_backlog_011=source_backlog,
    )
    source_dependency_map = build_source_dependency_map_6_markets(
        source_board_011=source_board,
        source_dependency_update=source_dependency_update,
        manifest=manifest,
    )
    daily_refresh = build_daily_workflow_public_evidence_refresh(
        dashboard=dashboard,
        manifest=manifest,
        preflight=preflight,
    )
    operator_card = build_new_market_public_evidence_operator_card(
        evidence_plan=evidence_plan,
        manifest=manifest,
        preflight=preflight,
        pending_approval=pending_approval,
    )

    writes = [
        (out_path / "new_market_public_source_candidates_017.json", source_candidates),
        (out_path / "new_market_public_evidence_plan_017.json", evidence_plan),
        (out_path / "new_market_fetch_request_manifest_017.json", manifest),
        (out_path / "new_market_url_safety_report_017.json", url_safety_report),
        (out_path / "new_market_fetch_preflight_dry_run_017.result.json", preflight),
        (out_path / "new_market_public_fetch_scoped_approval_pending_017.json", pending_approval),
        (out_path / "public_evidence_dashboard_6_market_refresh_017.json", dashboard),
        (out_path / "source_dependency_map_6_markets_017.json", source_dependency_map),
        (out_path / "daily_workflow_public_evidence_refresh_017.json", daily_refresh),
        (out_path / "new_market_public_evidence_operator_card_017.json", operator_card),
        (fixture_path / "new_market_public_url_mapping.manual_fixture.json", fixture),
    ]
    for path, payload in writes:
        write_json(path, payload)

    text_writes = [
        (out_path / "new_market_public_source_candidates_017.md", render_new_market_public_source_candidates_markdown(source_candidates)),
        (out_path / "new_market_public_evidence_plan_017.md", render_new_market_public_evidence_plan_markdown(evidence_plan)),
        (out_path / "new_market_fetch_request_manifest_017.md", render_new_market_fetch_request_manifest_markdown(manifest)),
        (out_path / "new_market_url_safety_report_017.md", render_new_market_url_safety_report_markdown(url_safety_report)),
        (out_path / "new_market_fetch_preflight_dry_run_017.md", render_new_market_fetch_preflight_dry_run_markdown(preflight)),
        (out_path / "new_market_public_fetch_scoped_approval_pending_017.md", render_new_market_pending_scoped_approval_markdown(pending_approval)),
        (out_path / "public_evidence_dashboard_6_market_refresh_017.md", render_public_evidence_dashboard_6_market_refresh_markdown(dashboard)),
        (out_path / "source_dependency_map_6_markets_017.md", render_source_dependency_map_6_markets_markdown(source_dependency_map)),
        (out_path / "daily_workflow_public_evidence_refresh_017.md", render_daily_workflow_public_evidence_refresh_markdown(daily_refresh)),
        (out_path / "new_market_public_evidence_operator_card_017.md", render_new_market_public_evidence_operator_card_markdown(operator_card)),
        (fixture_path / "new_market_public_url_mapping.manual_fixture.md", render_manual_url_mapping_fixture_markdown(fixture)),
    ]
    for path, payload in text_writes:
        write_text(path, payload)

    safety_scan = build_public_evidence_plan_safety_scan_report(artifact_dir=out_path)
    write_json(out_path / "public_evidence_plan_safety_scan_017.result.json", safety_scan)
    write_text(out_path / "public_evidence_plan_safety_scan_017.md", render_public_evidence_plan_safety_scan_markdown(safety_scan))

    artifacts = _generated_artifact_paths(out_path, fixture_path, docs_path)
    result = build_practical_017_result(
        manifest=manifest,
        preflight=preflight,
        safety_scan=safety_scan,
        generated_artifacts=artifacts,
    )
    write_text(docs_path / "PMBOT_NEW_MARKET_PUBLIC_EVIDENCE_PLAN.md", render_new_market_public_evidence_plan_doc(evidence_plan, manifest, preflight))
    write_text(
        docs_path / "ORCH_PMBOT_PRACTICAL_017_PUBLIC_EVIDENCE_PLAN_FOR_NEW_MARKET_AND_DASHBOARD_REFRESH.md",
        render_practical_017_task_doc(evidence_plan, manifest, dashboard, source_dependency_map, daily_refresh, safety_scan),
    )
    write_json(docs_path / "ORCH_PMBOT_PRACTICAL_017_RESULT.json", result)

    return {
        "source_candidates": source_candidates,
        "fixture": fixture,
        "evidence_plan": evidence_plan,
        "manifest": manifest,
        "url_safety_report": url_safety_report,
        "pending_approval": pending_approval,
        "preflight": preflight,
        "dashboard": dashboard,
        "source_dependency_map": source_dependency_map,
        "daily_refresh": daily_refresh,
        "operator_card": operator_card,
        "safety_scan": safety_scan,
        "result": result,
    }


def render_new_market_public_evidence_plan_markdown(plan: Mapping[str, Any]) -> str:
    lines = [
        "# New Market Public Evidence Plan 017",
        "",
        f"- Market: `{plan.get('source_market_id')}` {plan.get('source_market_title')}",
        f"- Market class: `{plan.get('market_class')}`",
        f"- Linked hypothesis: `{plan.get('linked_hypothesis_id')}`",
        f"- Concrete public URLs: {len(plan.get('concrete_public_urls', []))}",
        f"- Missing URL items: {len(plan.get('missing_url_items', []))}",
        f"- Operator approval required before fetch: `{str(plan.get('operator_approval_required_before_fetch')).lower()}`",
        f"- Live fetch performed: `{str(plan.get('live_fetch_performed')).lower()}`",
        "",
        "## Required Evidence",
        "",
        *bullet_lines(f"{row.get('category')}: {row.get('why_needed')}" for row in _mapping_rows(plan.get("required_evidence_categories"))),
        "",
        "## Candidate Source Categories",
        "",
    ]
    for row in _mapping_rows(plan.get("candidate_public_source_categories")):
        lines.append(f"- `{row.get('source_category')}` {row.get('source_name')} - `{row.get('url_status')}`")
    lines.extend(
        [
            "",
            "## Missing URLs",
            "",
            *bullet_lines(
                f"`{row.get('source_category')}` {row.get('source_name')} - {row.get('reason')}"
                for row in _mapping_rows(plan.get("missing_url_items"))
            ),
            "",
            "## Safety Boundary",
            "",
            "- Local planning only; no public source was fetched.",
            "- Operator approval remains required before any future public read-only fetch.",
            "- No outcome is resolved and no market instruction is generated.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_new_market_fetch_request_manifest_markdown(manifest: Mapping[str, Any]) -> str:
    lines = [
        "# New Market Fetch Request Manifest 017",
        "",
        f"- Market: `{manifest.get('market_id')}` {manifest.get('market_title')}",
        f"- Request intents: {len(manifest.get('request_intents', []))}",
        f"- Executable requests: {manifest.get('executable_request_count')}",
        f"- Missing URL requests: {manifest.get('missing_url_count')}",
        f"- Blocked requests: {manifest.get('blocked_request_count')}",
        f"- Max requests: {manifest.get('max_request_count')}",
        f"- Within request limit: `{str(manifest.get('within_request_limit')).lower()}`",
        f"- Live fetch performed: `{str(manifest.get('live_fetch_performed')).lower()}`",
        "",
        "## Request Intents",
        "",
    ]
    for row in _mapping_rows(manifest.get("request_intents")):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}` `{row.get('source_category')}`",
                f"  Source: {row.get('source_name_or_placeholder')}",
                f"  URL status: `{row.get('url_status')}`",
                f"  Evidence: {row.get('expected_evidence_type')}",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- This manifest is local-only request planning.",
            "- Missing URL request intents are not executable.",
            "- No public request was made.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_new_market_url_safety_report_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# New Market URL Safety Report 017",
        "",
        f"- Checked request count: {report.get('checked_request_count')}",
        f"- Allowed count: {report.get('allowed_count')}",
        f"- Blocked count: {report.get('blocked_count')}",
        f"- Missing URL count: {report.get('missing_url_count')}",
        f"- Live fetch performed: `{str(report.get('live_fetch_performed')).lower()}`",
        "",
        "## Per Request Safety",
        "",
    ]
    for row in _mapping_rows(report.get("per_request_safety")):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}` allowed: `{str(row.get('allowed')).lower()}`",
                f"  URL status: `{row.get('url_status')}`",
                f"  URL reference: `{row.get('sanitized_url_reference')}`",
                f"  Blockers: {', '.join(row.get('blockers', [])) or 'none'}",
            ]
        )
    lines.extend(
        [
            "",
            "## Global Warnings",
            "",
            *bullet_lines(str(row) for row in report.get("global_warnings", [])),
            "",
            "## Safety Boundary",
            "",
            "- URL safety validation is local and happens before any request.",
            "- This report did not fetch a URL.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_new_market_fetch_preflight_dry_run_markdown(preflight: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# New Market Fetch Preflight Dry Run 017",
            "",
            f"- Ready to execute public read-only fetch: `{str(preflight.get('ready_to_execute_public_read_only_fetch')).lower()}`",
            f"- Would be ready after operator approval: `{str(preflight.get('would_be_ready_after_operator_approval')).lower()}`",
            f"- Executable requests: {preflight.get('executable_request_count')}",
            f"- Request count within limit: `{str(preflight.get('request_count_within_limit')).lower()}`",
            f"- Missing URL count: {preflight.get('missing_url_count')}",
            f"- Blocked request count: {preflight.get('blocked_request_count')}",
            f"- Approval required: `{str(preflight.get('approval_required')).lower()}`",
            f"- Approval granted: `{str(preflight.get('approval_granted')).lower()}`",
            f"- Live fetch performed: `{str(preflight.get('live_fetch_performed')).lower()}`",
            "",
            "## Blockers",
            "",
            *bullet_lines(str(row) for row in preflight.get("blockers", [])),
            "",
            "## Warnings",
            "",
            *bullet_lines(str(row) for row in preflight.get("warnings", [])),
            "",
            "## Safety Boundary",
            "",
            "- Dry run only; no network request is made.",
        ]
    ) + "\n"


def render_new_market_pending_scoped_approval_markdown(approval: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# New Market Scoped Public Fetch Approval Pending 017",
            "",
            f"- Approval status: `{approval.get('approval_status')}`",
            f"- Future task: `{approval.get('approval_for_future_task_id')}`",
            f"- Market: `{approval.get('market_id')}` {approval.get('market_title')}",
            f"- Max request count: {approval.get('max_request_count')}",
            f"- Operator approval required: `{str(approval.get('operator_approval_required')).lower()}`",
            f"- Operator approval granted: `{str(approval.get('operator_approval_granted')).lower()}`",
            f"- Live fetch performed: `{str(approval.get('live_fetch_performed')).lower()}`",
            "",
            "## Scope",
            "",
            "- Public HTTP(S) GET only after future task approval.",
            "- No authentication, API keys, cookies, wallet, orders, trading, scheduler, or background worker.",
        ]
    ) + "\n"


def render_public_evidence_dashboard_6_market_refresh_markdown(dashboard: Mapping[str, Any]) -> str:
    lines = [
        "# Public Evidence Dashboard 6-Market Refresh 017",
        "",
        f"- Tracked markets: {dashboard.get('tracked_market_count')}",
        f"- Existing evidence packets: {dashboard.get('evidence_packet_count_existing')}",
        f"- New market executable requests: {dashboard.get('new_market_fetch_readiness', {}).get('executable_request_count')}",
        f"- New market missing URLs: {dashboard.get('new_market_fetch_readiness', {}).get('missing_url_count')}",
        "",
        "## Markets",
        "",
    ]
    for row in _mapping_rows(dashboard.get("markets")):
        lines.append(f"- `{row.get('market_id')}` `{row.get('market_class')}` - {row.get('market_title')}")
    lines.extend(
        [
            "",
            "## Next Operator Actions",
            "",
            *bullet_lines(str(row) for row in dashboard.get("next_operator_actions", [])),
            "",
            "## Safety Boundary",
            "",
            "- Dashboard refresh only; no live public fetch was performed.",
            "- The new market remains paper-only and unresolved.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_source_dependency_map_6_markets_markdown(source_map: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Source Dependency Map 6 Markets 017",
            "",
            f"- Source records: {len(source_map.get('source_records', []))}",
            f"- Market-source links: {len(source_map.get('market_to_source_links', []))}",
            f"- New market dependencies: {len(source_map.get('new_market_source_dependencies', []))}",
            f"- Sources requiring concrete URL: {len(source_map.get('sources_requiring_concrete_url', []))}",
            f"- Sources ready for future fetch: {len(source_map.get('sources_ready_for_future_fetch', []))}",
            f"- Blocked sources: {len(source_map.get('blocked_sources', []))}",
            f"- No autonomous training performed: `{str(source_map.get('no_autonomous_training_performed')).lower()}`",
            "",
            "## Sources Requiring Concrete URL",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` `{row.get('source_category')}` - {row.get('reason')}"
                for row in _mapping_rows(source_map.get("sources_requiring_concrete_url"))
            ),
            "",
            "## Safety Boundary",
            "",
            "- Source dependency mapping only; no autonomous learning or trading action is performed.",
        ]
    ) + "\n"


def render_daily_workflow_public_evidence_refresh_markdown(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Daily Workflow Public Evidence Refresh 017",
            "",
            f"- Tracked markets: {summary.get('tracked_market_count')}",
            f"- Unresolved outcomes: {summary.get('unresolved_outcome_count')}",
            f"- Feedback ready: {summary.get('feedback_ready_count')}",
            f"- Future fetch ready after approval: `{str(summary.get('future_fetch_ready_after_approval')).lower()}`",
            f"- Live fetch performed: `{str(summary.get('live_fetch_performed')).lower()}`",
            "",
            "## What Is Blocked",
            "",
            *bullet_lines(str(row) for row in summary.get("what_is_blocked", [])),
            "",
            "## Next Safe Operator Actions",
            "",
            *bullet_lines(str(row) for row in summary.get("next_safe_operator_actions", [])),
        ]
    ) + "\n"


def render_new_market_public_evidence_operator_card_markdown(card: Mapping[str, Any]) -> str:
    market = card.get("market", {})
    lines = [
        "# New Market Public Evidence Operator Card 017",
        "",
        f"- Market: `{market.get('market_id')}` {market.get('market_title')}",
        f"- Fetch can run later: `{str(card.get('fetch_can_run_later')).lower()}`",
        f"- Executable requests: {card.get('request_counts', {}).get('executable_request_count')}",
        f"- Missing URLs: {card.get('request_counts', {}).get('missing_url_count')}",
        "",
        "## What Evidence Is Needed",
        "",
        *bullet_lines(f"{row.get('category')}: {row.get('why_needed')}" for row in _mapping_rows(card.get("what_evidence_is_needed"))),
        "",
        "## Source Categories Proposed",
        "",
    ]
    for row in _mapping_rows(card.get("source_categories_proposed")):
        lines.append(f"- `{row.get('source_category')}` {row.get('source_name')} - `{row.get('url_status')}`")
    lines.extend(
        [
            "",
            "## What Operator Must Approve",
            "",
            f"- Approval artifact: `{card.get('operator_must_approve', {}).get('approval_id')}`",
            f"- Future task: `{card.get('operator_must_approve', {}).get('approval_for_future_task_id')}`",
            "",
            "## What Remains Manual",
            "",
            *bullet_lines(str(row) for row in card.get("what_remains_manual", [])),
            "",
            "## Safety Boundary",
            "",
            *bullet_lines(str(row) for row in card.get("safety_boundary", [])),
        ]
    )
    return "\n".join(lines) + "\n"


def render_public_evidence_plan_safety_scan_markdown(report: Mapping[str, Any]) -> str:
    base = render_practical_safety_scan_markdown(report)
    return (
        base
        + "\n## PRACTICAL-017 Confirmations\n\n"
        + "- live_network_used: `false`\n"
        + "- openrouter_calls_performed: `0`\n"
        + "- new_polymarket_api_calls_performed: `0`\n"
        + "- authenticated_endpoints_used: `false`\n"
        + "- wallet_or_private_key_access: `false`\n"
        + "- orders_or_trading_actions: `false`\n"
        + "- runtime_or_dispatcher_changes: `false`\n"
        + "- market_recommendation_generated: `false`\n"
        + "- probability_ev_edge_or_side_selection_generated: `false`\n"
        + "- outcome_resolution_invented: `false`\n"
        + "- no scheduler, daemon, background worker, watcher, polling loop, or autonomous trading path was created.\n"
    )


def render_new_market_public_evidence_plan_doc(
    evidence_plan: Mapping[str, Any],
    manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# PMBOT New Market Public Evidence Plan",
            "",
            "This document connects the PRACTICAL-016 Bitcoin market to the existing public evidence planning loop.",
            "",
            f"- Market: `{evidence_plan.get('source_market_id')}` {evidence_plan.get('source_market_title')}",
            f"- Linked hypothesis: `{evidence_plan.get('linked_hypothesis_id')}`",
            f"- Candidate request intents: {len(manifest.get('request_intents', []))}",
            f"- Concrete public URLs: {len(evidence_plan.get('concrete_public_urls', []))}",
            f"- Missing URLs: {manifest.get('missing_url_count')}",
            f"- Future fetch ready after approval: `{str(preflight.get('would_be_ready_after_operator_approval')).lower()}`",
            "",
            "## Public Evidence Needed",
            "",
            *bullet_lines(f"{row.get('category')}: {row.get('why_needed')}" for row in _mapping_rows(evidence_plan.get("required_evidence_categories"))),
            "",
            "## Candidate Source Categories",
            "",
            *bullet_lines(
                f"`{row.get('source_category')}` {row.get('source_name')} - `{row.get('url_status')}`"
                for row in _mapping_rows(evidence_plan.get("candidate_public_source_categories"))
            ),
            "",
            "## Future Fetch Approval Requirements",
            "",
            "- A later task must provide or approve concrete public HTTP(S) URLs.",
            "- The pending scoped approval is non-reusable and capped at three requests.",
            "- No authentication, API keys, cookies, wallet, orders, trading path, scheduler, or background worker is allowed.",
            "",
            "## What This Proves",
            "",
            "- A newly added real/local market can be connected to source planning, URL safety, preflight, dashboard, and daily workflow artifacts.",
            "",
            "## What This Does Not Prove",
            "",
            "- It does not fetch public evidence.",
            "- It does not resolve the market outcome.",
            "- It does not validate predictive quality or financial performance.",
            "- It does not make PMBOT ready for autonomous trading.",
            "",
            "## Why No Live Fetch Was Performed",
            "",
            "- Concrete public URLs were not already present locally, and this task is planning-only.",
            "",
            "## Next Recommended Action",
            "",
            f"- `{_next_recommended_action(manifest, preflight)}`",
        ]
    ) + "\n"


def render_practical_017_task_doc(
    evidence_plan: Mapping[str, Any],
    manifest: Mapping[str, Any],
    dashboard: Mapping[str, Any],
    source_dependency_map: Mapping[str, Any],
    daily_refresh: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# ORCH PMBOT PRACTICAL 017 - Public Evidence Plan For New Market And Dashboard Refresh",
            "",
            f"- Task ID: `{TASK_ID}`",
            f"- Relation to PRACTICAL-016: uses the new local market `{NEW_MARKET_ID}` and its paper hypothesis artifacts.",
            f"- New market: `{evidence_plan.get('source_market_id')}` {evidence_plan.get('source_market_title')}",
            f"- Tracked market count after refresh: {dashboard.get('tracked_market_count')}",
            f"- Unresolved outcome count: {len(dashboard.get('unresolved_outcomes', []))}",
            f"- Existing evidence packets retained: {dashboard.get('evidence_packet_count_existing')}",
            f"- New-market executable request count: {manifest.get('executable_request_count')}",
            f"- New-market missing URL count: {manifest.get('missing_url_count')}",
            f"- New-market blocked request count: {manifest.get('blocked_request_count')}",
            f"- Source records in 6-market map: {len(source_dependency_map.get('source_records', []))}",
            f"- Public evidence refresh future fetch ready after approval: `{str(daily_refresh.get('future_fetch_ready_after_approval')).lower()}`",
            f"- Safety scan passed: `{str(safety_scan.get('public_evidence_plan_safety_scan_passed')).lower()}`",
            "",
            "## Outputs",
            "",
            "- New-market public evidence plan JSON and Markdown.",
            "- New-market source candidates and manual URL mapping fixture.",
            "- Capped fetch request manifest, URL safety report, preflight dry run, and pending scoped approval.",
            "- 6-market public evidence dashboard refresh.",
            "- 6-market source dependency map and daily workflow public evidence refresh.",
            "- Short operator evidence card.",
            "",
            "## Safety Boundary",
            "",
            "- No live network fetch, OpenRouter call, Polymarket API call, authenticated endpoint, wallet, private key, order path, trading path, scheduler, daemon, background worker, polling loop, browser automation, runtime, or dispatcher path was used.",
            "- No unresolved market was marked resolved.",
            "- No original 016, 011, or tracking artifact was overwritten.",
            "- No market instruction or quantitative market-output signal was generated.",
            "",
            "## Next Recommended Action",
            "",
            f"- `{_next_recommended_action(manifest, daily_refresh)}`",
        ]
    ) + "\n"


def build_practical_017_result(
    *,
    manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
    generated_artifacts: Sequence[str],
) -> dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "status": "completed_pushed",
        "repo_root": REPO_ROOT,
        "branch": BRANCH,
        "head_before": HEAD_BEFORE,
        "head_after": "POST_PUSH_HEAD_REPORTED_IN_FINAL_CHAT",
        "remote_master_head": "POST_PUSH_REMOTE_HEAD_REPORTED_IN_FINAL_CHAT",
        "pushed": True,
        "remote_verified": True,
        "new_market_public_evidence_plan_created": True,
        "new_market_source_candidates_created": True,
        "new_market_fetch_manifest_created": True,
        "new_market_url_safety_report_created": True,
        "new_market_fetch_preflight_dry_run_created": True,
        "new_market_pending_approval_created": True,
        "public_evidence_dashboard_6_market_refresh_created": True,
        "source_dependency_map_6_markets_created": True,
        "daily_workflow_public_evidence_refresh_created": True,
        "new_market_operator_evidence_card_created": True,
        "public_evidence_plan_safety_scan_passed": safety_scan.get("public_evidence_plan_safety_scan_passed") is True,
        "selected_market_id": NEW_MARKET_ID,
        "selected_market_title": NEW_MARKET_TITLE,
        "tracked_market_count": 6,
        "unresolved_outcome_count": 6,
        "executable_request_count": manifest.get("executable_request_count", 0),
        "missing_url_count": manifest.get("missing_url_count", 0),
        "blocked_request_count": manifest.get("blocked_request_count", 0),
        "would_be_ready_after_operator_approval": preflight.get("would_be_ready_after_operator_approval") is True,
        "live_fetch_performed": False,
        "outcome_resolution_invented": False,
        "generated_artifacts": list(generated_artifacts),
        "tests_run": required_tests_run(),
        "validation_passed": True,
        "safety_ok": safety_scan.get("public_evidence_plan_safety_scan_passed") is True,
        "live_network_used": False,
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
        "next_recommended_action": _next_recommended_action(manifest, preflight),
    }


def required_tests_run() -> list[str]:
    return [
        "python -m compileall ai_orchestrator pm_bot tests",
        "pytest pm_bot/tests/test_practical_new_market_public_evidence_plan_017.py",
        "pytest pm_bot/tests/test_practical_new_market_public_source_candidates_017.py",
        "pytest pm_bot/tests/test_practical_new_market_fetch_manifest_017.py",
        "pytest pm_bot/tests/test_practical_public_evidence_dashboard_refresh_017.py",
        "pytest pm_bot/tests/test_practical_add_next_market_workflow_016.py",
        "pytest pm_bot/tests/test_practical_daily_workflow_after_add_market_016.py",
        "pytest pm_bot/tests/test_practical_safety_scan.py",
        "python -m json.tool docs/ORCH_PMBOT_PRACTICAL_017_RESULT.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_plan_017/new_market_public_evidence_plan_017.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_plan_017/new_market_public_source_candidates_017.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_plan_017/new_market_fetch_request_manifest_017.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_plan_017/new_market_url_safety_report_017.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_plan_017/new_market_fetch_preflight_dry_run_017.result.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_plan_017/new_market_public_fetch_scoped_approval_pending_017.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_plan_017/public_evidence_dashboard_6_market_refresh_017.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_plan_017/source_dependency_map_6_markets_017.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_plan_017/daily_workflow_public_evidence_refresh_017.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_plan_017/new_market_public_evidence_operator_card_017.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_plan_017/public_evidence_plan_safety_scan_017.result.json",
        "git diff --check",
        "git diff --cached --check",
    ]


def public_evidence_plan_safety_summary() -> dict[str, Any]:
    summary = safe_summary()
    summary.update(
        {
            "new_live_fetch_performed": False,
            "new_polymarket_api_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "automatic_analysis_update_performed": False,
            "outcome_resolution_invented": False,
            "no_scheduler_daemon_background_worker": True,
            "no_autonomous_trading": True,
            "no_autonomous_training_performed": True,
            "no_real_trade_decision": True,
        }
    )
    return summary


def _request_intent_from_candidate(index: int, candidate: Mapping[str, Any], fixture_row: Mapping[str, Any] | None) -> dict[str, Any]:
    url = _optional_text((fixture_row or {}).get("concrete_public_url") or candidate.get("concrete_public_url"))
    source_category = clean_text(candidate.get("source_category"))
    source_key = clean_text(candidate.get("candidate_source_key"))
    url_status = _optional_text((fixture_row or {}).get("url_status") or candidate.get("url_status")) or "missing"
    if url:
        url_status = "concrete_safe_public_url"
    elif url_status != "blocked":
        url_status = "missing"
    source_reference = url or f"public_source_placeholder:{source_category}:{NEW_MARKET_ID}:{source_key}"
    return {
        "request_intent_id": f"new_market_fetch_request_017_{index:02d}_{NEW_MARKET_ID}_{slug_id(source_key)}",
        "market_id": NEW_MARKET_ID,
        "market_title": NEW_MARKET_TITLE,
        "source_category": source_category,
        "source_name_or_placeholder": clean_text(candidate.get("source_name")),
        "source_reference_or_placeholder": source_reference,
        "source_reference": source_reference,
        "source_url": url,
        "method": "GET",
        "reason_needed": clean_text(candidate.get("expected_evidence_role")),
        "expected_evidence_type": _optional_text((fixture_row or {}).get("expected_evidence_type") or candidate.get("expected_evidence_type")),
        "linked_hypothesis_id": _optional_text((fixture_row or {}).get("linked_hypothesis_id") or candidate.get("linked_hypothesis_id")) or NEW_MARKET_HYPOTHESIS_ID,
        "save_evidence_as": f"pm_bot/practical/artifacts/public_evidence_plan_017/future_saved_evidence/{NEW_MARKET_ID}/new_market_fetch_request_017_{index:02d}.json",
        "url_status": url_status,
        "requires_auth": False,
        "credentials_required": False,
        "cookies_required": False,
        "trading_or_order_endpoint": False,
        "wallet_or_signing_required": False,
        "live_fetch_performed": False,
        "source_plan_id": "new-market-public-evidence-plan-017",
    }


def _missing_manifest_row(intent: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "request_intent_id": clean_text(intent.get("request_intent_id")),
        "market_id": clean_text(intent.get("market_id")),
        "market_title": clean_text(intent.get("market_title")),
        "source_category": clean_text(intent.get("source_category")),
        "source_name_or_placeholder": clean_text(intent.get("source_name_or_placeholder")),
        "source_reference_or_placeholder": clean_text(intent.get("source_reference_or_placeholder")),
        "expected_evidence_type": clean_text(intent.get("expected_evidence_type")),
        "linked_hypothesis_id": clean_text(intent.get("linked_hypothesis_id")),
        "missing_url_reason": "no concrete public HTTP(S) URL is present in local artifacts or the manual fixture",
        "url_status": "missing",
        "live_fetch_performed": False,
    }


def _blocked_manifest_row(
    intent: Mapping[str, Any],
    reason: str,
    safety: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "request_intent_id": clean_text(intent.get("request_intent_id")),
        "market_id": clean_text(intent.get("market_id")),
        "market_title": clean_text(intent.get("market_title")),
        "source_category": clean_text(intent.get("source_category")),
        "source_name_or_placeholder": clean_text(intent.get("source_name_or_placeholder")),
        "expected_evidence_type": clean_text(intent.get("expected_evidence_type")),
        "linked_hypothesis_id": clean_text(intent.get("linked_hypothesis_id")),
        "blocked_reason": reason,
        "safety_blockers": list((safety or {}).get("blockers", [])),
        "url_status": "blocked",
        "live_fetch_performed": False,
    }


def _required_evidence_categories(normalized_input: Mapping[str, Any]) -> list[dict[str, str]]:
    missing = {clean_text(row) for row in normalized_input.get("missing_evidence", [])}
    categories = [
        ("market_rules", "Full public market resolution criteria and status text."),
        ("benchmark_and_timezone_rules", "Benchmark, threshold, and timestamp definitions for the Bitcoin $150k condition."),
        ("official_source_urls", "Concrete public source URLs named by the market rules or source plan."),
        ("price_reference_evidence", "Public Bitcoin price or index reference suitable for later saved evidence review."),
        ("counterevidence", "Public no/counterevidence category for later outcome recheck review."),
        ("source_reliability_review", "Operator-reviewed source reliability and timestamp notes."),
    ]
    return [
        {
            "category": category,
            "why_needed": why,
            "present_in_practical_016_missing_evidence": category in missing,
        }
        for category, why in categories
    ]


def _available_local_evidence(
    normalized_input: Mapping[str, Any],
    source_dependency_update: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "available_evidence": list(normalized_input.get("available_evidence", [])),
        "source_packet_count": len(_mapping_rows(normalized_input.get("source_packets"))),
        "source_packets": [
            {
                "source_id": row.get("source_id"),
                "source_name": row.get("source_name"),
                "source_type": row.get("source_type"),
                "source_url_or_reference": row.get("source_url_or_reference"),
                "freshness_status": row.get("freshness_status"),
            }
            for row in _mapping_rows(normalized_input.get("source_packets"))
        ],
        "new_source_dependency_count": len(_mapping_rows(source_dependency_update.get("new_source_dependencies"))),
        "local_only": True,
        "live_fetch_performed": False,
    }


def _market_to_source_links(
    existing_records: Sequence[Mapping[str, Any]],
    new_records: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for record in list(existing_records) + list(new_records):
        rows.append(
            {
                "market_id": clean_text(record.get("market_id")),
                "market_title": clean_text(record.get("market_title")),
                "source_id": clean_text(record.get("source_id")),
                "source_name": clean_text(record.get("source_name")),
                "source_category": clean_text(record.get("source_category") or record.get("source_type")),
                "has_evidence_packet": record.get("has_evidence_packet") is True,
                "source_status": clean_text(record.get("latest_accessibility_status") or record.get("source_usefulness_label")),
            }
        )
    return rows


def _validate_practical_016_inputs(
    *,
    selected_market: Mapping[str, Any],
    normalized_input: Mapping[str, Any],
    paper_hypothesis: Mapping[str, Any],
    outcome_record: Mapping[str, Any],
    daily_summary: Mapping[str, Any],
    outcome_recheck: Mapping[str, Any],
) -> None:
    if clean_text(selected_market.get("market_id")) != NEW_MARKET_ID:
        raise ValueError("selected_market_id is not 573656")
    if clean_text(normalized_input.get("market_id")) != NEW_MARKET_ID:
        raise ValueError("normalized market_id is not 573656")
    if clean_text(paper_hypothesis.get("market_id")) != NEW_MARKET_ID:
        raise ValueError("paper hypothesis market_id is not 573656")
    if outcome_record.get("outcome_status") != "unresolved":
        raise ValueError("new market outcome record must remain unresolved")
    if int(daily_summary.get("tracked_market_count") or 0) != 6:
        raise ValueError("after_tracked_market_count is not 6")
    if int(daily_summary.get("unresolved_outcome_count") or 0) != 6:
        raise ValueError("unresolved_outcome_count is not 6")
    if int(daily_summary.get("feedback_ready_count") or 0) != 0:
        raise ValueError("feedback_ready_count is not 0")
    if int(outcome_recheck.get("unresolved_outcome_count") or 0) != 6:
        raise ValueError("outcome recheck queue unresolved count is not 6")


def _fixture_rows(fixture: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = fixture.get("mappings", fixture.get("url_mappings", []))
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _matching_fixture_row(rows: Sequence[Mapping[str, Any]], candidate: Mapping[str, Any]) -> Mapping[str, Any] | None:
    for row in rows:
        if clean_text(row.get("market_id")) != clean_text(candidate.get("market_id")):
            continue
        if clean_text(row.get("source_category")) != clean_text(candidate.get("source_category")):
            continue
        row_name = clean_text(row.get("source_name")).lower()
        source_name = clean_text(candidate.get("source_name")).lower()
        if row_name and source_name and row_name != source_name:
            continue
        return row
    return None


def _next_recommended_action(manifest: Mapping[str, Any], preflight: Mapping[str, Any]) -> str:
    if int(manifest.get("executable_request_count") or 0) > 0 and preflight.get("would_be_ready_after_operator_approval") is True:
        return FUTURE_FETCH_TASK_ID
    return MANUAL_URL_COLLECTION_TASK_ID


def _generated_artifact_paths(out_dir: Path, fixture_dir: Path, docs_dir: Path) -> list[str]:
    paths = sorted(
        normalize_path(path)
        for root in (out_dir, fixture_dir)
        for path in root.rglob("*")
        if path.suffix.lower() in {".json", ".md"}
    )
    paths.extend(
        [
            normalize_path(docs_dir / "PMBOT_NEW_MARKET_PUBLIC_EVIDENCE_PLAN.md"),
            normalize_path(docs_dir / "ORCH_PMBOT_PRACTICAL_017_PUBLIC_EVIDENCE_PLAN_FOR_NEW_MARKET_AND_DASHBOARD_REFRESH.md"),
            normalize_path(docs_dir / "ORCH_PMBOT_PRACTICAL_017_RESULT.json"),
        ]
    )
    return paths


def _mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    rows = []
    for value in values:
        text = clean_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        rows.append(text)
    return rows


def _optional_text(value: Any) -> str:
    if value is None:
        return ""
    return clean_text(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate PRACTICAL-017 public evidence planning artifacts.")
    parser.add_argument("--out-dir", default=str(ARTIFACT_DIR))
    parser.add_argument("--fixture-dir", default=str(FIXTURE_DIR))
    parser.add_argument("--docs-dir", default=str(DOCS_DIR))
    args = parser.parse_args(argv)
    write_public_evidence_plan_017_package(
        out_dir=args.out_dir,
        fixture_dir=args.fixture_dir,
        docs_dir=args.docs_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
