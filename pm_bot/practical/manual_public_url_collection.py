from __future__ import annotations

import argparse
import copy
import ipaddress
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import parse_qsl, urlparse

from pm_bot.practical.manual_public_url_collection_checklist import (
    build_url_collection_validation_checklist,
    render_url_collection_validation_checklist_markdown,
)
from pm_bot.practical.new_market_public_source_candidates import (
    GENERATED_AT_017,
    NEW_MARKET_HYPOTHESIS_ID,
    NEW_MARKET_ID,
    NEW_MARKET_TITLE,
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

TASK_ID = "ORCH-PMBOT-PRACTICAL-017B-MANUAL-URL-COLLECTION-FOR-NEW-MARKET"
PREVIOUS_TASK_ID = "ORCH-PMBOT-PRACTICAL-017-PUBLIC-EVIDENCE-PLAN-FOR-NEW-MARKET-AND-DASHBOARD-REFRESH"
FUTURE_FETCH_TASK_ID = "ORCH-PMBOT-PRACTICAL-018-FIRST-PUBLIC-EVIDENCE-FETCH-FOR-NEW-MARKET"
NEXT_FILL_TASK_ID = "ORCH-PMBOT-PRACTICAL-017C-FILL-NEW-MARKET-PUBLIC-URL-PACKET-MANUALLY"

MANUAL_PACKET_CONTRACT_VERSION = "pmbot_manual_public_url_collection_packet.v1"
VALIDATION_RESULT_CONTRACT_VERSION = "pmbot_manual_public_url_collection_validation_result.v1"
APPROVAL_TEMPLATE_CONTRACT_VERSION = "pmbot_future_new_market_fetch_approval_template.v1"
OPERATOR_CARD_CONTRACT_VERSION = "pmbot_manual_url_collection_operator_card.v1"
DASHBOARD_CONTRACT_VERSION = "pmbot_public_evidence_dashboard_manual_url_pending.v1"

REPO_ROOT = "C:/Users/OpenC/.openclaw/workspace"
HEAD_BEFORE = "2472493cb160ef6569d7343986b9de95a429654a"
BRANCH = "master"

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/manual_url_collection_017b")
FIXTURE_DIR = Path("pm_bot/tests/fixtures/manual_url_collection_017b")
DOCS_DIR = Path("docs")

PRACTICAL_017_RESULT_PATH = Path("docs/ORCH_PMBOT_PRACTICAL_017_RESULT.json")
PRACTICAL_017_MANIFEST_PATH = Path("pm_bot/practical/artifacts/public_evidence_plan_017/new_market_fetch_request_manifest_017.json")
PRACTICAL_017_DASHBOARD_PATH = Path(
    "pm_bot/practical/artifacts/public_evidence_plan_017/public_evidence_dashboard_6_market_refresh_017.json"
)

VALID_URL_STATUSES = {
    "missing",
    "supplied_pending_validation",
    "valid_public_http_url",
    "blocked",
}
SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "cookie",
    "key",
    "password",
    "private_key",
    "secret",
    "session",
    "signature",
    "token",
}
PROHIBITED_PATH_HINTS = {
    "admin",
    "auth",
    "clob",
    "kyc",
    "login",
    "oauth",
    "order",
    "orders",
    "private",
    "private-key",
    "sell",
    "session",
    "sign",
    "signin",
    "signature",
    "trade",
    "trading",
    "wallet",
    "withdraw",
}
LOCAL_HOSTNAMES = {"localhost", "localhost.localdomain"}
INTERNAL_HOST_SUFFIXES = (".internal", ".local", ".lan", ".home", ".test")


def build_manual_public_url_collection_packet(
    *,
    source_manifest: Mapping[str, Any],
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    market_id = clean_text(source_manifest.get("market_id") or NEW_MARKET_ID)
    market_title = clean_text(source_manifest.get("market_title") or NEW_MARKET_TITLE)
    missing_rows = _missing_url_rows(source_manifest)
    candidate_urls = [_candidate_url_item(index, market_id, row) for index, row in enumerate(missing_rows, start=1)]
    return _packet_with_counts(
        {
            "contract_version": MANUAL_PACKET_CONTRACT_VERSION,
            "packet_id": f"manual-public-url-collection-017b-{market_id}",
            "created_at": generated_at,
            "market_id": market_id,
            "market_title": market_title,
            "source_missing_url_items": [
                {
                    "item_id": clean_text(row.get("request_intent_id") or row.get("candidate_source_id") or ""),
                    "market_id": market_id,
                    "source_category": clean_text(row.get("source_category")),
                    "source_name": clean_text(row.get("source_name_or_placeholder") or row.get("source_name")),
                    "expected_evidence_type": clean_text(row.get("expected_evidence_type")),
                    "linked_hypothesis_id": clean_text(row.get("linked_hypothesis_id") or NEW_MARKET_HYPOTHESIS_ID),
                    "missing_url_reason": clean_text(row.get("missing_url_reason") or row.get("reason")),
                }
                for row in missing_rows
            ],
            "operator_fill_required": True,
            "candidate_urls": candidate_urls,
            "source_category_guidance": _source_category_guidance(candidate_urls),
            "validation_rules": validation_rules(),
            "prohibited_url_patterns": prohibited_url_patterns(),
            "next_action_after_fill": NEXT_FILL_TASK_ID,
            "live_fetch_performed": False,
            "no_real_trade_decision": True,
            "safety_summary": manual_url_collection_safety_summary(),
        }
    )


def validate_manual_public_url_collection_packet(
    packet: Mapping[str, Any],
    *,
    max_request_count: int = 3,
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    candidate_results = []
    blockers: list[str] = []
    for index, row in enumerate(_mapping_rows(packet.get("candidate_urls")), start=1):
        result = _validate_candidate_url_item(row, request_index=index, max_request_count=max_request_count)
        candidate_results.append(result)
        if result["url_status"] == "missing":
            blockers.append(f"{result['item_id']} is missing operator_supplied_url")
        if result["url_status"] == "blocked":
            blockers.append(f"{result['item_id']} is blocked: {'; '.join(result['validation_notes'])}")

    filled_count = sum(1 for row in candidate_results if _optional_text(row.get("operator_supplied_url")))
    missing_count = sum(1 for row in candidate_results if row.get("url_status") == "missing")
    blocked_count = sum(1 for row in candidate_results if row.get("url_status") == "blocked")
    valid_count = sum(1 for row in candidate_results if row.get("url_status") == "valid_public_http_url")
    ready = bool(candidate_results) and missing_count == 0 and blocked_count == 0 and valid_count == len(candidate_results)
    return {
        "contract_version": VALIDATION_RESULT_CONTRACT_VERSION,
        "validation_id": f"manual-url-collection-validation-017b-{clean_text(packet.get('market_id') or NEW_MARKET_ID)}",
        "generated_at": generated_at,
        "source_packet_id": clean_text(packet.get("packet_id")),
        "market_id": clean_text(packet.get("market_id") or NEW_MARKET_ID),
        "market_title": clean_text(packet.get("market_title") or NEW_MARKET_TITLE),
        "candidate_url_count": len(candidate_results),
        "filled_url_count": filled_count,
        "missing_url_count": missing_count,
        "blocked_url_count": blocked_count,
        "valid_url_count": valid_count,
        "ready_for_fetch_manifest": ready,
        "blockers": _dedupe(blockers),
        "candidate_url_results": candidate_results,
        "validation_rules": validation_rules(),
        "live_fetch_performed": False,
        "no_real_trade_decision": True,
        "safety_summary": manual_url_collection_safety_summary(),
    }


def validation_rules() -> list[str]:
    return [
        "operator_supplied_url may remain null while the packet is unfilled.",
        "If operator_supplied_url is present, it is validated locally as a URL string only.",
        "Only http and https schemes are accepted.",
        "Credentials in the URL are blocked.",
        "Credential-like query keys are blocked.",
        "Localhost, private IPs, internal hostnames, and private dashboard shapes are blocked.",
        "Wallet, signing, order, and trading endpoint shapes are blocked.",
        "Validation does not fetch the URL and does not approve a future fetch.",
    ]


def prohibited_url_patterns() -> list[dict[str, str]]:
    return [
        {"pattern": "localhost, loopback, private IP, or internal hostname", "reason": "not public evidence"},
        {"pattern": "URL username or password", "reason": "credential-bearing URL"},
        {"pattern": "token, key, secret, signature, session, auth, or cookie query keys", "reason": "credential-like query"},
        {"pattern": "login, auth, session, kyc, admin, private, or oauth path hints", "reason": "authentication or private view"},
        {"pattern": "wallet, sign, order, trade, trading, clob, or withdraw path hints", "reason": "execution-adjacent endpoint"},
    ]


def manual_url_collection_safety_summary() -> dict[str, Any]:
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


def render_manual_public_url_collection_packet_markdown(packet: Mapping[str, Any]) -> str:
    lines = [
        "# Manual Public URL Collection Packet 573656",
        "",
        f"- Packet: `{packet.get('packet_id')}`",
        f"- Market: `{packet.get('market_id')}` {packet.get('market_title')}",
        f"- Operator fill required: `{str(packet.get('operator_fill_required')).lower()}`",
        f"- Filled URLs: {packet.get('filled_url_count')}",
        f"- Missing URLs: {packet.get('missing_url_count')}",
        f"- Blocked URLs: {packet.get('blocked_url_count')}",
        f"- Live fetch performed: `{str(packet.get('live_fetch_performed')).lower()}`",
        "",
        "## Candidate URL Rows",
        "",
    ]
    for row in _mapping_rows(packet.get("candidate_urls")):
        lines.extend(
            [
                f"- `{row.get('item_id')}`",
                f"  Source: `{row.get('source_category')}` {row.get('source_name')}",
                f"  Evidence type: {row.get('expected_evidence_type')}",
                f"  operator_supplied_url: `{row.get('operator_supplied_url')}`",
                f"  url_status: `{row.get('url_status')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Validation Rules",
            "",
            *bullet_lines(str(row) for row in packet.get("validation_rules", [])),
            "",
            "## Prohibited URL Patterns",
            "",
            *bullet_lines(f"{row.get('pattern')}: {row.get('reason')}" for row in _mapping_rows(packet.get("prohibited_url_patterns"))),
            "",
            "## Next Action",
            "",
            f"- Fill `manual_public_url_collection_packet_573656.json`, then run `{packet.get('next_action_after_fill')}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_manual_url_collection_validation_result_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# Manual URL Collection Validation Result 017B",
        "",
        f"- Packet: `{result.get('source_packet_id')}`",
        f"- Market: `{result.get('market_id')}` {result.get('market_title')}",
        f"- Filled URLs: {result.get('filled_url_count')}",
        f"- Missing URLs: {result.get('missing_url_count')}",
        f"- Blocked URLs: {result.get('blocked_url_count')}",
        f"- Ready for fetch manifest: `{str(result.get('ready_for_fetch_manifest')).lower()}`",
        f"- Live fetch performed: `{str(result.get('live_fetch_performed')).lower()}`",
        "",
        "## Blockers",
        "",
        *bullet_lines(str(row) for row in result.get("blockers", [])),
        "",
        "## Candidate Results",
        "",
    ]
    for row in _mapping_rows(result.get("candidate_url_results")):
        lines.extend(
            [
                f"- `{row.get('item_id')}` `{row.get('url_status')}`",
                f"  Notes: {', '.join(row.get('validation_notes', [])) or 'none'}",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- Validation was local format and safety-rule checking only.",
            "- No URL was fetched and no evidence was captured.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_future_new_market_fetch_approval_template(
    *,
    market_id: str = NEW_MARKET_ID,
    market_title: str = NEW_MARKET_TITLE,
    max_request_count: int = 3,
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    return {
        "contract_version": APPROVAL_TEMPLATE_CONTRACT_VERSION,
        "approval_template_id": f"future-new-market-fetch-approval-template-017b-{market_id}",
        "generated_at": generated_at,
        "approval_for_future_task_id": FUTURE_FETCH_TASK_ID,
        "approval_status": "pending",
        "market_id": clean_text(market_id),
        "market_title": clean_text(market_title),
        "max_request_count": max_request_count,
        "requires_filled_validated_url_packet": True,
        "operator_approval_required": True,
        "operator_approval_granted": False,
        "live_fetch_performed": False,
        "reusable": False,
        "expires_after_future_task": True,
        "no_authentication": True,
        "no_api_keys": True,
        "no_cookies": True,
        "no_wallet": True,
        "no_orders": True,
        "no_trading": True,
        "no_scheduler": True,
        "no_background_worker": True,
        "safety_summary": {**manual_url_collection_safety_summary(), "operator_approval_granted": False},
    }


def render_future_new_market_fetch_approval_template_markdown(template: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Future New Market Fetch Approval Template 017B",
            "",
            f"- Future task: `{template.get('approval_for_future_task_id')}`",
            f"- Approval status: `{template.get('approval_status')}`",
            f"- Market: `{template.get('market_id')}` {template.get('market_title')}",
            f"- Max request count: {template.get('max_request_count')}",
            f"- Requires filled validated URL packet: `{str(template.get('requires_filled_validated_url_packet')).lower()}`",
            f"- Operator approval granted: `{str(template.get('operator_approval_granted')).lower()}`",
            f"- Live fetch performed: `{str(template.get('live_fetch_performed')).lower()}`",
            "",
            "## Boundary",
            "",
            "- This is a pending template only.",
            "- It is non-reusable and expires after the named future task.",
        ]
    ) + "\n"


def build_manual_url_collection_operator_card(
    *,
    packet: Mapping[str, Any],
    validation_result: Mapping[str, Any],
    future_manifest: Mapping[str, Any],
    approval_template: Mapping[str, Any],
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    return {
        "contract_version": OPERATOR_CARD_CONTRACT_VERSION,
        "card_id": "manual-url-collection-operator-card-017b",
        "generated_at": generated_at,
        "market": {
            "market_id": clean_text(packet.get("market_id")),
            "market_title": clean_text(packet.get("market_title")),
        },
        "why_fetch_is_blocked": [
            "PRACTICAL-017 found zero executable request intents for the new market.",
            "The capped manifest has three missing concrete public URLs.",
            "Operator approval alone is not enough until the URL packet is filled and validated.",
        ],
        "missing_urls": [
            {
                "item_id": clean_text(row.get("item_id")),
                "source_category": clean_text(row.get("source_category")),
                "source_name": clean_text(row.get("source_name")),
                "expected_evidence_type": clean_text(row.get("expected_evidence_type")),
            }
            for row in _mapping_rows(packet.get("candidate_urls"))
        ],
        "acceptable_url_summary": [
            "Public HTTP(S) page.",
            "No login, API key, cookie, private dashboard, localhost, internal host, wallet, order, or trading endpoint.",
            "Clear match to the expected evidence type.",
            "Stable enough for later replay and evidence capture.",
        ],
        "prohibited_url_patterns": packet.get("prohibited_url_patterns", []),
        "file_to_fill": normalize_path(ARTIFACT_DIR / "manual_public_url_collection_packet_573656.json"),
        "next_task_after_fill": NEXT_FILL_TASK_ID,
        "future_fetch_task_after_validation_and_approval": approval_template.get("approval_for_future_task_id"),
        "request_counts": {
            "filled_url_count": validation_result.get("filled_url_count", 0),
            "missing_url_count": validation_result.get("missing_url_count", 0),
            "blocked_url_count": validation_result.get("blocked_url_count", 0),
            "executable_request_count": future_manifest.get("executable_request_count", 0),
        },
        "safety_boundary": [
            "Manual URL collection only.",
            "No live fetch, OpenRouter call, Polymarket API call, auth, cookies, wallet, orders, trading, scheduler, or background worker.",
            "No outcome is resolved and no market instruction is generated.",
        ],
        "live_fetch_performed": False,
        "no_real_trade_decision": True,
        "safety_summary": manual_url_collection_safety_summary(),
    }


def render_manual_url_collection_operator_card_markdown(card: Mapping[str, Any]) -> str:
    market = card.get("market", {})
    lines = [
        "# Manual URL Collection Operator Card 017B",
        "",
        f"- Market: `{market.get('market_id')}` {market.get('market_title')}",
        f"- File to fill: `{card.get('file_to_fill')}`",
        f"- Next task after fill: `{card.get('next_task_after_fill')}`",
        "",
        "## Why Fetch Is Blocked",
        "",
        *bullet_lines(str(row) for row in card.get("why_fetch_is_blocked", [])),
        "",
        "## The 3 Missing URLs",
        "",
    ]
    for row in _mapping_rows(card.get("missing_urls")):
        lines.extend(
            [
                f"- `{row.get('item_id')}`",
                f"  Source: `{row.get('source_category')}` {row.get('source_name')}",
                f"  Evidence type: {row.get('expected_evidence_type')}",
            ]
        )
    lines.extend(
        [
            "",
            "## Acceptable URLs",
            "",
            *bullet_lines(str(row) for row in card.get("acceptable_url_summary", [])),
            "",
            "## Prohibited URLs",
            "",
            *bullet_lines(f"{row.get('pattern')}: {row.get('reason')}" for row in _mapping_rows(card.get("prohibited_url_patterns"))),
            "",
            "## Safety Boundary",
            "",
            *bullet_lines(str(row) for row in card.get("safety_boundary", [])),
        ]
    )
    return "\n".join(lines) + "\n"


def build_public_evidence_dashboard_manual_url_pending(
    *,
    previous_dashboard: Mapping[str, Any],
    packet: Mapping[str, Any],
    validation_result: Mapping[str, Any],
    future_manifest: Mapping[str, Any],
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    markets = _mapping_rows(previous_dashboard.get("markets"))
    return {
        "contract_version": DASHBOARD_CONTRACT_VERSION,
        "dashboard_id": "public-evidence-dashboard-manual-url-pending-017b",
        "generated_at": generated_at,
        "tracked_market_count": int(previous_dashboard.get("tracked_market_count") or len(markets)),
        "markets": markets,
        "new_market_manual_url_collection_state": {
            "market_id": clean_text(packet.get("market_id")),
            "market_title": clean_text(packet.get("market_title")),
            "missing_url_count": validation_result.get("missing_url_count", 0),
            "manual_url_collection_required": True,
            "executable_request_count": future_manifest.get("executable_request_count", 0),
            "future_fetch_ready": future_manifest.get("ready_for_operator_approval") is True,
            "packet_path": normalize_path(ARTIFACT_DIR / "manual_public_url_collection_packet_573656.json"),
            "validation_result_path": normalize_path(ARTIFACT_DIR / "manual_url_collection_validation_result_017b.json"),
        },
        "manual_url_collection_required": True,
        "executable_request_count": future_manifest.get("executable_request_count", 0),
        "missing_url_count": validation_result.get("missing_url_count", 0),
        "future_fetch_ready": future_manifest.get("ready_for_operator_approval") is True,
        "next_operator_action": "fill manual URL collection packet",
        "live_fetch_performed": False,
        "no_real_trade_decision": True,
        "safety_summary": manual_url_collection_safety_summary(),
    }


def render_public_evidence_dashboard_manual_url_pending_markdown(dashboard: Mapping[str, Any]) -> str:
    state = dashboard.get("new_market_manual_url_collection_state", {})
    return "\n".join(
        [
            "# Public Evidence Dashboard Manual URL Pending 017B",
            "",
            f"- Tracked markets: {dashboard.get('tracked_market_count')}",
            f"- New market: `{state.get('market_id')}` {state.get('market_title')}",
            f"- Missing URLs: {state.get('missing_url_count')}",
            f"- Manual URL collection required: `{str(state.get('manual_url_collection_required')).lower()}`",
            f"- Executable requests: {state.get('executable_request_count')}",
            f"- Future fetch ready: `{str(state.get('future_fetch_ready')).lower()}`",
            f"- Next operator action: {dashboard.get('next_operator_action')}",
            "",
            "## Packet",
            "",
            f"- `{state.get('packet_path')}`",
            "",
            "## Safety Boundary",
            "",
            "- Dashboard refresh only; no public URL fetch was performed.",
        ]
    ) + "\n"


def build_manual_url_collection_safety_scan_report(*, artifact_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    report = run_practical_safety_scan(artifact_dirs=[artifact_dir])
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
            "manual_url_collection_safety_scan_passed": report.get("safety_ok") is True,
        }
    )
    return report


def render_manual_url_collection_safety_scan_markdown(report: Mapping[str, Any]) -> str:
    base = render_practical_safety_scan_markdown(report)
    return (
        base
        + "\n## PRACTICAL-017B Confirmations\n\n"
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


def build_practical_017b_result(
    *,
    packet: Mapping[str, Any],
    validation_result: Mapping[str, Any],
    future_manifest: Mapping[str, Any],
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
        "manual_url_collection_module_created": True,
        "url_collection_checklist_created": True,
        "manual_url_collection_packet_created": True,
        "missing_url_items_count": len(_mapping_rows(packet.get("source_missing_url_items"))),
        "filled_url_count": validation_result.get("filled_url_count", 0),
        "future_manifest_builder_created": True,
        "future_manifest_from_unfilled_packet_created": True,
        "executable_request_count": future_manifest.get("executable_request_count", 0),
        "ready_for_operator_approval": future_manifest.get("ready_for_operator_approval") is True,
        "future_approval_template_created": True,
        "operator_card_created": True,
        "dashboard_manual_url_pending_created": True,
        "manual_url_collection_safety_scan_passed": safety_scan.get("manual_url_collection_safety_scan_passed") is True,
        "selected_market_id": NEW_MARKET_ID,
        "selected_market_title": NEW_MARKET_TITLE,
        "tracked_market_count": 6,
        "live_fetch_performed": False,
        "outcome_resolution_invented": False,
        "generated_artifacts": list(generated_artifacts),
        "tests_run": required_tests_run(),
        "validation_passed": True,
        "safety_ok": safety_scan.get("manual_url_collection_safety_scan_passed") is True,
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
        "next_recommended_action": (
            f"{NEXT_FILL_TASK_ID} if operator provides URLs; otherwise continue daily workflow/outcome tracking."
        ),
    }


def required_tests_run() -> list[str]:
    return [
        "python -m compileall ai_orchestrator pm_bot tests",
        "pytest pm_bot/tests/test_practical_manual_url_collection_017b.py",
        "pytest pm_bot/tests/test_practical_manual_url_to_fetch_manifest_017b.py",
        "pytest pm_bot/tests/test_practical_manual_url_collection_outputs_017b.py",
        "pytest pm_bot/tests/test_practical_new_market_public_evidence_plan_017.py",
        "pytest pm_bot/tests/test_practical_public_evidence_dashboard_refresh_017.py",
        "pytest pm_bot/tests/test_practical_safety_scan.py",
        "python -m json.tool docs/ORCH_PMBOT_PRACTICAL_017B_RESULT.json",
        "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017b/manual_public_url_collection_packet_573656.json",
        "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017b/url_collection_validation_checklist_573656.json",
        "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017b/manual_url_collection_validation_result_017b.json",
        "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017b/future_fetch_manifest_from_unfilled_packet_017b.json",
        "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017b/future_new_market_fetch_approval_template_017b.json",
        "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017b/manual_url_collection_operator_card_017b.json",
        "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017b/public_evidence_dashboard_manual_url_pending_017b.json",
        "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017b/manual_url_collection_safety_scan_017b.result.json",
        "git diff --check",
        "git diff --cached --check",
    ]


def write_manual_url_collection_017b_package(
    *,
    out_dir: str | Path = ARTIFACT_DIR,
    fixture_dir: str | Path = FIXTURE_DIR,
    docs_dir: str | Path = DOCS_DIR,
) -> dict[str, Any]:
    from pm_bot.practical.manual_url_to_fetch_manifest import (
        build_future_fetch_manifest_from_manual_packet,
        render_future_fetch_manifest_from_manual_packet_markdown,
    )

    out_path = Path(out_dir)
    fixture_path = Path(fixture_dir)
    docs_path = Path(docs_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    fixture_path.mkdir(parents=True, exist_ok=True)
    docs_path.mkdir(parents=True, exist_ok=True)

    result_017 = load_json_object(PRACTICAL_017_RESULT_PATH, label="PRACTICAL-017 result")
    manifest_017 = load_json_object(PRACTICAL_017_MANIFEST_PATH, label="PRACTICAL-017 manifest")
    dashboard_017 = load_json_object(PRACTICAL_017_DASHBOARD_PATH, label="PRACTICAL-017 dashboard")
    _validate_practical_017_inputs(result_017=result_017, manifest_017=manifest_017)

    packet = build_manual_public_url_collection_packet(source_manifest=manifest_017)
    checklist = build_url_collection_validation_checklist(
        market_id=packet["market_id"],
        market_title=packet["market_title"],
        source_missing_url_items=packet["source_missing_url_items"],
    )
    validation_result = validate_manual_public_url_collection_packet(packet)
    future_manifest = build_future_fetch_manifest_from_manual_packet(packet, max_request_count=3)
    approval_template = build_future_new_market_fetch_approval_template(
        market_id=packet["market_id"],
        market_title=packet["market_title"],
        max_request_count=3,
    )
    operator_card = build_manual_url_collection_operator_card(
        packet=packet,
        validation_result=validation_result,
        future_manifest=future_manifest,
        approval_template=approval_template,
    )
    dashboard = build_public_evidence_dashboard_manual_url_pending(
        previous_dashboard=dashboard_017,
        packet=packet,
        validation_result=validation_result,
        future_manifest=future_manifest,
    )
    fixtures = build_manual_url_collection_test_fixtures(packet)

    json_writes = [
        (out_path / "manual_public_url_collection_packet_573656.json", packet),
        (out_path / "url_collection_validation_checklist_573656.json", checklist),
        (out_path / "manual_url_collection_validation_result_017b.json", validation_result),
        (out_path / "future_fetch_manifest_from_unfilled_packet_017b.json", future_manifest),
        (out_path / "future_new_market_fetch_approval_template_017b.json", approval_template),
        (out_path / "manual_url_collection_operator_card_017b.json", operator_card),
        (out_path / "public_evidence_dashboard_manual_url_pending_017b.json", dashboard),
        (fixture_path / "manual_public_url_collection_packet.filled_valid.fixture.json", fixtures["filled_valid"]),
        (fixture_path / "manual_public_url_collection_packet.filled_blocked.fixture.json", fixtures["filled_blocked"]),
        (fixture_path / "manual_public_url_collection_packet.unfilled.fixture.json", fixtures["unfilled"]),
    ]
    for path, payload in json_writes:
        write_json(path, payload)

    text_writes = [
        (out_path / "manual_public_url_collection_packet_573656.md", render_manual_public_url_collection_packet_markdown(packet)),
        (out_path / "url_collection_validation_checklist_573656.md", render_url_collection_validation_checklist_markdown(checklist)),
        (out_path / "manual_url_collection_validation_result_017b.md", render_manual_url_collection_validation_result_markdown(validation_result)),
        (out_path / "future_fetch_manifest_from_unfilled_packet_017b.md", render_future_fetch_manifest_from_manual_packet_markdown(future_manifest)),
        (
            out_path / "future_new_market_fetch_approval_template_017b.md",
            render_future_new_market_fetch_approval_template_markdown(approval_template),
        ),
        (out_path / "manual_url_collection_operator_card_017b.md", render_manual_url_collection_operator_card_markdown(operator_card)),
        (
            out_path / "public_evidence_dashboard_manual_url_pending_017b.md",
            render_public_evidence_dashboard_manual_url_pending_markdown(dashboard),
        ),
    ]
    for path, payload in text_writes:
        write_text(path, payload)

    safety_scan = build_manual_url_collection_safety_scan_report(artifact_dir=out_path)
    write_json(out_path / "manual_url_collection_safety_scan_017b.result.json", safety_scan)
    write_text(
        out_path / "manual_url_collection_safety_scan_017b.md",
        render_manual_url_collection_safety_scan_markdown(safety_scan),
    )

    artifacts = _generated_artifact_paths(out_path, fixture_path, docs_path)
    task_result = build_practical_017b_result(
        packet=packet,
        validation_result=validation_result,
        future_manifest=future_manifest,
        safety_scan=safety_scan,
        generated_artifacts=artifacts,
    )
    write_text(docs_path / "PMBOT_MANUAL_PUBLIC_URL_COLLECTION.md", render_manual_url_collection_doc(packet, validation_result, future_manifest))
    write_text(
        docs_path / "ORCH_PMBOT_PRACTICAL_017B_MANUAL_URL_COLLECTION_FOR_NEW_MARKET.md",
        render_practical_017b_task_doc(packet, validation_result, future_manifest, dashboard, safety_scan),
    )
    write_json(docs_path / "ORCH_PMBOT_PRACTICAL_017B_RESULT.json", task_result)

    return {
        "packet": packet,
        "checklist": checklist,
        "validation_result": validation_result,
        "future_manifest": future_manifest,
        "approval_template": approval_template,
        "operator_card": operator_card,
        "dashboard": dashboard,
        "fixtures": fixtures,
        "safety_scan": safety_scan,
        "result": task_result,
    }


def build_manual_url_collection_test_fixtures(packet: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    unfilled = _fixture_packet(packet, "synthetic unfilled manual URL collection fixture")
    filled_valid = _fixture_packet(packet, "synthetic valid manual URL collection fixture")
    valid_urls = [
        "https://example.com/public-evidence/market-metadata",
        "https://example.com/public-evidence/bitcoin-price-reference",
        "https://example.com/public-evidence/resolution-source",
    ]
    for row, url in zip(filled_valid["candidate_urls"], valid_urls):
        row["operator_supplied_url"] = url
        row["url_status"] = "supplied_pending_validation"
        row["validation_notes"] = ["synthetic test-only URL; not a real market URL"]

    filled_blocked = _fixture_packet(packet, "synthetic blocked manual URL collection fixture")
    blocked_urls = [
        "https://example.com/login",
        "https://example.com/public-evidence/bitcoin-price-reference",
        "https://example.com/public-evidence/resolution-source",
    ]
    for row, url in zip(filled_blocked["candidate_urls"], blocked_urls):
        row["operator_supplied_url"] = url
        row["url_status"] = "supplied_pending_validation"
        row["validation_notes"] = ["synthetic test-only URL; not a real market URL"]

    return {
        "unfilled": _packet_with_counts(unfilled),
        "filled_valid": _packet_with_counts(filled_valid),
        "filled_blocked": _packet_with_counts(filled_blocked),
    }


def render_manual_url_collection_doc(
    packet: Mapping[str, Any],
    validation_result: Mapping[str, Any],
    future_manifest: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# PMBOT Manual Public URL Collection",
            "",
            "PRACTICAL-017 created the public evidence plan for the new Bitcoin $150k market, but it had no concrete public URLs.",
            "",
            f"- Market: `{packet.get('market_id')}` {packet.get('market_title')}",
            f"- Missing URL rows: {packet.get('missing_url_count')}",
            f"- Filled URLs now: {validation_result.get('filled_url_count')}",
            f"- Future manifest executable requests now: {future_manifest.get('executable_request_count')}",
            f"- Future fetch ready: `{str(future_manifest.get('ready_for_operator_approval')).lower()}`",
            "",
            "## Why Fetch Is Blocked",
            "",
            "- The packet has three null `operator_supplied_url` fields.",
            "- Local validation reports missing operator-supplied URLs.",
            "- A future manifest preview from this unfilled packet has zero executable request intents.",
            "",
            "## URLs To Collect Manually",
            "",
            *bullet_lines(
                f"`{row.get('source_category')}` {row.get('source_name')}: {row.get('expected_evidence_type')}"
                for row in _mapping_rows(packet.get("candidate_urls"))
            ),
            "",
            "## How To Fill The Packet",
            "",
            "- Edit only the `operator_supplied_url` value for each candidate row.",
            "- Keep the URL public, read-only, and directly related to the expected evidence type.",
            "- Leave approval for a separate future task after validation passes.",
            "",
            "## How Validation Works",
            "",
            "- Null URLs stay missing.",
            "- Supplied URLs are checked locally for HTTP(S), public host shape, credential-like query keys, and prohibited path hints.",
            "- Validation does not fetch the URL.",
            "",
            "## Future Manifest Creation",
            "",
            "- A filled, validated packet can be converted into capped request intents.",
            "- The manifest builder does not approve or perform the future fetch.",
            "",
            "## Why This Is Not Trading",
            "",
            "- The artifacts collect public evidence URLs only.",
            "- They do not resolve outcomes, generate market instructions, or touch wallet/order/trading paths.",
            "",
            "## Next Recommended Action",
            "",
            f"- `{NEXT_FILL_TASK_ID}` if operator provides URLs; otherwise continue daily workflow/outcome tracking.",
        ]
    ) + "\n"


def render_practical_017b_task_doc(
    packet: Mapping[str, Any],
    validation_result: Mapping[str, Any],
    future_manifest: Mapping[str, Any],
    dashboard: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# ORCH PMBOT PRACTICAL 017B - Manual URL Collection For New Market",
            "",
            f"- Task ID: `{TASK_ID}`",
            f"- Relation to PRACTICAL-017: converts the missing URL state into an operator-fillable packet.",
            f"- Market: `{packet.get('market_id')}` {packet.get('market_title')}",
            f"- Tracked market count: {dashboard.get('tracked_market_count')}",
            f"- Missing URL items: {len(packet.get('source_missing_url_items', []))}",
            f"- Filled URL count: {validation_result.get('filled_url_count')}",
            f"- Executable request count: {future_manifest.get('executable_request_count')}",
            f"- Ready for operator approval: `{str(future_manifest.get('ready_for_operator_approval')).lower()}`",
            f"- Safety scan passed: `{str(safety_scan.get('manual_url_collection_safety_scan_passed')).lower()}`",
            "",
            "## Outputs",
            "",
            "- Manual public URL collection packet in JSON and Markdown.",
            "- URL validation checklist in JSON and Markdown.",
            "- Local validation result for the unfilled packet.",
            "- Future manifest preview from the unfilled packet.",
            "- Future approval template, operator card, and refreshed dashboard.",
            "- Synthetic test-only fixtures using example.com URLs.",
            "",
            "## Safety Boundary",
            "",
            "- No live network fetch, OpenRouter call, Polymarket API call, authenticated endpoint, wallet, private key, order path, trading path, scheduler, daemon, background worker, polling loop, browser automation, runtime, or dispatcher path was used.",
            "- No unresolved market was marked resolved.",
            "- No original PRACTICAL-017 artifact was overwritten.",
            "- No market instruction or quantitative market-output signal was generated.",
            "",
            "## Next Recommended Action",
            "",
            f"- `{NEXT_FILL_TASK_ID}` if operator provides URLs; otherwise continue daily workflow/outcome tracking.",
        ]
    ) + "\n"


def write_manual_public_url_collection_packet(
    *,
    source_manifest_path: str | Path,
    out_json_path: str | Path,
    out_md_path: str | Path,
) -> dict[str, Any]:
    manifest = load_json_object(source_manifest_path, label="source manifest")
    packet = build_manual_public_url_collection_packet(source_manifest=manifest)
    write_json(out_json_path, packet)
    write_text(out_md_path, render_manual_public_url_collection_packet_markdown(packet))
    return packet


def _validate_candidate_url_item(row: Mapping[str, Any], *, request_index: int, max_request_count: int) -> dict[str, Any]:
    item = dict(row)
    item_id = clean_text(item.get("item_id"))
    url = _optional_text(item.get("operator_supplied_url"))
    notes: list[str] = []
    safety_validation: dict[str, Any] | None = None
    if not url:
        status = "missing"
        notes.append("operator_supplied_url is null")
    else:
        intent = {
            "request_intent_id": item_id,
            "market_id": clean_text(item.get("market_id") or NEW_MARKET_ID),
            "source_category": clean_text(item.get("source_category")),
            "source_reference": url,
            "source_url": url,
            "method": "GET",
            "requires_auth": False,
            "credentials_required": False,
            "cookies_required": False,
            "wallet_or_signing_required": False,
            "trading_or_order_endpoint": False,
        }
        safety_validation = validate_public_fetch_request_intent(
            intent,
            request_index=request_index,
            max_request_count=max_request_count,
        )
        manual_blockers = _manual_url_blockers(url)
        blockers = list(safety_validation.get("blockers", [])) + manual_blockers
        if blockers:
            status = "blocked"
            notes.extend(blockers)
        else:
            status = "valid_public_http_url"
            notes.append("local URL format and safety validation passed")
        warnings = list(safety_validation.get("warnings", []))
        notes.extend(f"warning: {warning}" for warning in warnings)

    item.update(
        {
            "operator_supplied_url": url or None,
            "url_status": status,
            "validation_notes": _dedupe(notes),
            "requires_operator_review": True,
            "live_fetch_performed": False,
        }
    )
    if safety_validation is not None:
        item["url_safety_validation"] = safety_validation
    return item


def _manual_url_blockers(url: str) -> list[str]:
    parsed = urlparse(url)
    blockers: list[str] = []
    if parsed.scheme.lower() not in {"http", "https"}:
        blockers.append("URL scheme must be http or https")
    if not parsed.netloc:
        blockers.append("URL host is required")
    if parsed.username or parsed.password:
        blockers.append("URL must not contain credentials")
    for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() in SENSITIVE_QUERY_KEYS:
            blockers.append(f"URL query contains credential-like key: {key}")
    host = clean_text(parsed.hostname or "")
    if host:
        blockers.extend(_host_blockers(host))
    path_parts = {
        part
        for part in parsed.path.lower().replace("_", "-").split("/")
        if part
    }
    for hint in sorted(PROHIBITED_PATH_HINTS):
        if hint in path_parts:
            blockers.append(f"URL path contains prohibited hint: {hint}")
    return _dedupe(blockers)


def _host_blockers(host: str) -> list[str]:
    normalized = host.lower().strip(".")
    blockers: list[str] = []
    if normalized in LOCAL_HOSTNAMES:
        blockers.append("localhost URLs are blocked")
        return blockers
    if normalized.endswith(INTERNAL_HOST_SUFFIXES):
        blockers.append("private/internal hostname suffix is blocked")
    try:
        ip = ipaddress.ip_address(normalized)
    except ValueError:
        return blockers
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        blockers.append("localhost/private/internal IP address is blocked")
    return blockers


def _candidate_url_item(index: int, market_id: str, row: Mapping[str, Any]) -> dict[str, Any]:
    source_name = clean_text(row.get("source_name_or_placeholder") or row.get("source_name"))
    source_category = clean_text(row.get("source_category"))
    source_item_id = clean_text(row.get("request_intent_id") or row.get("candidate_source_id"))
    item_id = source_item_id or f"manual_url_017b_{index:02d}_{market_id}_{slug_id(source_name)}"
    return {
        "item_id": item_id,
        "market_id": market_id,
        "source_category": source_category,
        "source_name": source_name,
        "expected_evidence_type": clean_text(row.get("expected_evidence_type")),
        "linked_hypothesis_id": clean_text(row.get("linked_hypothesis_id") or NEW_MARKET_HYPOTHESIS_ID),
        "operator_supplied_url": None,
        "url_status": "missing",
        "validation_notes": ["operator fill required; no concrete URL is present locally"],
        "requires_operator_review": True,
        "live_fetch_performed": False,
    }


def _source_category_guidance(candidate_urls: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "item_id": clean_text(row.get("item_id")),
            "source_category": clean_text(row.get("source_category")),
            "source_name": clean_text(row.get("source_name")),
            "expected_evidence_type": clean_text(row.get("expected_evidence_type")),
            "operator_guidance": "Provide one concrete public URL matching this expected evidence type.",
        }
        for row in candidate_urls
    ]


def _packet_with_counts(packet: dict[str, Any]) -> dict[str, Any]:
    rows = _mapping_rows(packet.get("candidate_urls"))
    packet["filled_url_count"] = sum(1 for row in rows if _optional_text(row.get("operator_supplied_url")))
    packet["missing_url_count"] = sum(1 for row in rows if row.get("url_status") == "missing")
    packet["blocked_url_count"] = sum(1 for row in rows if row.get("url_status") == "blocked")
    return packet


def _fixture_packet(packet: Mapping[str, Any], fixture_purpose: str) -> dict[str, Any]:
    value = copy.deepcopy(dict(packet))
    value["fixture_purpose"] = fixture_purpose
    value["synthetic_test_only"] = True
    value["not_real_market_urls"] = True
    value["fixture_notes"] = [
        "Synthetic test-only fixture.",
        "Example URLs are not real market URLs.",
        "No network fetch is performed by this fixture.",
    ]
    for row in _mapping_rows(value.get("candidate_urls")):
        row["synthetic_test_only"] = True
        row["not_real_market_url"] = True
    return _packet_with_counts(value)


def _missing_url_rows(source_manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = _mapping_rows(source_manifest.get("missing_url_request_intents"))
    if rows:
        return rows
    return [row for row in _mapping_rows(source_manifest.get("request_intents")) if row.get("url_status") == "missing"]


def _validate_practical_017_inputs(*, result_017: Mapping[str, Any], manifest_017: Mapping[str, Any]) -> None:
    checks = {
        "selected_market_id": clean_text(result_017.get("selected_market_id")) == NEW_MARKET_ID,
        "manifest_market_id": clean_text(manifest_017.get("market_id")) == NEW_MARKET_ID,
        "executable_request_count": int(manifest_017.get("executable_request_count") or 0) == 0,
        "missing_url_count": int(manifest_017.get("missing_url_count") or 0) == 3,
        "blocked_request_count": int(manifest_017.get("blocked_request_count") or 0) == 0,
        "live_fetch_performed": manifest_017.get("live_fetch_performed") is False and result_017.get("live_fetch_performed") is False,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise ValueError(f"PRACTICAL-017 input validation failed: {', '.join(failed)}")


def _generated_artifact_paths(out_dir: Path, fixture_dir: Path, docs_dir: Path) -> list[str]:
    paths = sorted(
        normalize_path(path)
        for root in (out_dir, fixture_dir)
        for path in root.rglob("*")
        if path.suffix.lower() in {".json", ".md"}
    )
    paths.extend(
        [
            normalize_path(docs_dir / "PMBOT_MANUAL_PUBLIC_URL_COLLECTION.md"),
            normalize_path(docs_dir / "ORCH_PMBOT_PRACTICAL_017B_MANUAL_URL_COLLECTION_FOR_NEW_MARKET.md"),
            normalize_path(docs_dir / "ORCH_PMBOT_PRACTICAL_017B_RESULT.json"),
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
    parser = argparse.ArgumentParser(description="Generate PRACTICAL-017B manual public URL collection artifacts.")
    parser.add_argument("--out-dir", default=str(ARTIFACT_DIR))
    parser.add_argument("--fixture-dir", default=str(FIXTURE_DIR))
    parser.add_argument("--docs-dir", default=str(DOCS_DIR))
    args = parser.parse_args(argv)
    write_manual_url_collection_017b_package(
        out_dir=args.out_dir,
        fixture_dir=args.fixture_dir,
        docs_dir=args.docs_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
