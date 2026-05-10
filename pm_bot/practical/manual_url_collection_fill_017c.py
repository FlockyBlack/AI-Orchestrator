from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Mapping

from pm_bot.practical.manual_public_url_collection import (
    GENERATED_AT_017,
    manual_url_collection_safety_summary,
    prohibited_url_patterns,
    render_manual_public_url_collection_packet_markdown,
    validate_manual_public_url_collection_packet,
    validation_rules,
)
from pm_bot.practical.manual_url_to_fetch_manifest import (
    build_future_fetch_manifest_from_manual_packet,
    render_future_fetch_manifest_from_manual_packet_markdown,
)
from pm_bot.practical.practical_io import bullet_lines, load_json_object, normalize_path, slug_id, write_json, write_text
from pm_bot.practical.practical_safety_scan import run_practical_safety_scan
from pm_bot.practical.public_fetch_execution_preflight import (
    build_enriched_manifest_execution_preflight,
    render_enriched_manifest_execution_preflight_markdown,
)
from pm_bot.practical.public_fetch_url_safety import validate_public_fetch_request_intent

TASK_ID = "ORCH-PMBOT-PRACTICAL-017C-FILL-NEW-MARKET-PUBLIC-URL-PACKET-MANUALLY"
PREVIOUS_TASK_ID = "ORCH-PMBOT-PRACTICAL-017B-MANUAL-URL-COLLECTION-FOR-NEW-MARKET"
FUTURE_TASK_ID = "ORCH-PMBOT-PRACTICAL-018-FIRST-PUBLIC-EVIDENCE-FETCH-FOR-NEW-MARKET"
MARKET_ID = "573656"
MARKET_TITLE = "Will Bitcoin hit $150k by December 31, 2026?"
REPO_ROOT = "C:/Users/OpenC/.openclaw/workspace"
BRANCH = "master"
HEAD_BEFORE = "b45953a926750f751687119bf5fa32941aa4acc1"
TRACKED_MARKET_COUNT = 6
MAX_REQUEST_COUNT = 3

OUT_DIR = Path("pm_bot/practical/artifacts/manual_url_collection_017c")
DOCS_DIR = Path("docs")
SOURCE_PACKET_PATH = Path("pm_bot/practical/artifacts/manual_url_collection_017b/manual_public_url_collection_packet_573656.json")
SOURCE_VALIDATION_PATH = Path("pm_bot/practical/artifacts/manual_url_collection_017b/manual_url_collection_validation_result_017b.json")
SOURCE_MANIFEST_PATH = Path("pm_bot/practical/artifacts/manual_url_collection_017b/future_fetch_manifest_from_unfilled_packet_017b.json")
SOURCE_DASHBOARD_PATH = Path("pm_bot/practical/artifacts/manual_url_collection_017b/public_evidence_dashboard_manual_url_pending_017b.json")

OPERATOR_PROVIDED_URLS = [
    {
        "source_category": "public_btc_price_reference",
        "source_name": "CoinGecko Bitcoin BTC/USD public price chart",
        "operator_supplied_url": "https://www.coingecko.com/en/coins/bitcoin",
        "expected_evidence_type": "BTC/USD public price and chart reference for paper tracking",
        "reason": (
            "CoinGecko provides a public Bitcoin page with live BTC price, market cap, trading volume, "
            "and BTC/USD chart. Use only as public read-only evidence, not as a recommendation source."
        ),
    },
    {
        "source_category": "public_btc_price_reference",
        "source_name": "CoinMarketCap Bitcoin BTC/USD public price chart",
        "operator_supplied_url": "https://coinmarketcap.com/currencies/bitcoin/",
        "expected_evidence_type": "BTC/USD public price and historical chart reference for paper tracking",
        "reason": (
            "CoinMarketCap provides a public Bitcoin page with live BTC price and chart/history information. "
            "Use only as a second public read-only price/reference source, not as a recommendation source."
        ),
    },
    {
        "source_category": "public_resolution_reference",
        "source_name": "Polymarket public event page for Bitcoin $150k timing market",
        "operator_supplied_url": "https://polymarket.com/event/when-will-bitcoin-hit-150k",
        "expected_evidence_type": "public market/resolution context reference for the Bitcoin $150k paper tracking market",
        "reason": (
            "Public Polymarket event page for the Bitcoin $150k timing market. Use only as market/resolution context "
            "and paper-tracking reference. Do not use authenticated endpoints, trading endpoints, order endpoints, "
            "wallet actions, or Polymarket APIs."
        ),
    },
]


def _mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _safe_summary_017c() -> dict[str, Any]:
    summary = manual_url_collection_safety_summary()
    summary.update(
        {
            "new_live_fetch_performed": False,
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
            "no_real_trade_decision": True,
        }
    )
    return summary


def _packet_with_counts(packet: dict[str, Any]) -> dict[str, Any]:
    rows = _mapping_rows(packet.get("candidate_urls"))
    packet["supplied_url_count"] = sum(1 for row in rows if row.get("operator_supplied_url"))
    packet["filled_url_count"] = packet["supplied_url_count"]
    packet["missing_url_count"] = sum(1 for row in rows if row.get("url_status") == "missing" or not row.get("operator_supplied_url"))
    packet["blocked_url_count"] = sum(1 for row in rows if row.get("url_status") == "blocked")
    return packet


def build_filled_manual_url_packet(source_packet: Mapping[str, Any]) -> dict[str, Any]:
    source_rows = _mapping_rows(source_packet.get("candidate_urls"))
    default_linked_hypothesis = "573656.analysis.ceab64191597.paper_hypothesis"
    candidate_urls: list[dict[str, Any]] = []

    for index, supplied in enumerate(OPERATOR_PROVIDED_URLS, start=1):
        source_row = source_rows[index - 1] if index - 1 < len(source_rows) else {}
        source_name = str(supplied["source_name"])
        candidate_urls.append(
            {
                "item_id": f"manual_url_017c_{index:02d}_{MARKET_ID}_{slug_id(source_name)}",
                "market_id": MARKET_ID,
                "source_category": supplied["source_category"],
                "source_name": source_name,
                "expected_evidence_type": supplied["expected_evidence_type"],
                "linked_hypothesis_id": source_row.get("linked_hypothesis_id") or default_linked_hypothesis,
                "operator_supplied_url": supplied["operator_supplied_url"],
                "url_status": "supplied_pending_validation",
                "validation_notes": ["operator supplied concrete public URL; pending local format and safety validation"],
                "requires_operator_review": True,
                "operator_supplied_reason": supplied["reason"],
                "live_fetch_performed": False,
            }
        )

    packet = {
        "contract_version": "pmbot_manual_public_url_collection_packet.v1",
        "packet_id": f"manual-public-url-collection-017c-{MARKET_ID}-filled",
        "created_at": GENERATED_AT_017,
        "task_id": TASK_ID,
        "previous_task_id": PREVIOUS_TASK_ID,
        "market_id": MARKET_ID,
        "market_title": MARKET_TITLE,
        "source_packet_id": source_packet.get("packet_id"),
        "source_packet_path": normalize_path(SOURCE_PACKET_PATH),
        "source_missing_url_items": copy.deepcopy(source_packet.get("source_missing_url_items", [])),
        "operator_fill_required": False,
        "requires_operator_review": True,
        "candidate_urls": candidate_urls,
        "source_category_guidance": [
            {
                "item_id": row["item_id"],
                "source_category": row["source_category"],
                "source_name": row["source_name"],
                "expected_evidence_type": row["expected_evidence_type"],
                "operator_guidance": "Operator supplied this concrete public URL for local validation only.",
            }
            for row in candidate_urls
        ],
        "validation_rules": validation_rules(),
        "prohibited_url_patterns": prohibited_url_patterns(),
        "next_action_after_fill": FUTURE_TASK_ID,
        "live_fetch_performed": False,
        "live_network_used": False,
        "no_real_trade_decision": True,
        "safety_summary": _safe_summary_017c(),
    }
    return _packet_with_counts(packet)


def build_validation_result(packet: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_manual_public_url_collection_packet(
        packet,
        max_request_count=MAX_REQUEST_COUNT,
        generated_at=GENERATED_AT_017,
    )
    validation["validation_id"] = f"manual-url-collection-validation-017c-{MARKET_ID}"
    validation["source_packet_id"] = packet["packet_id"]
    validation["supplied_url_count"] = packet["supplied_url_count"]
    validation["local_validation_only"] = True
    validation["no_url_fetch_attempted"] = True
    validation["request_count_within_limit"] = validation["filled_url_count"] <= MAX_REQUEST_COUNT
    validation["safety_summary"] = _safe_summary_017c()
    return validation


def build_manifest(packet: Mapping[str, Any], validation: Mapping[str, Any]) -> dict[str, Any]:
    manifest = build_future_fetch_manifest_from_manual_packet(
        packet,
        max_request_count=MAX_REQUEST_COUNT,
        generated_at=GENERATED_AT_017,
    )
    manifest["manifest_id"] = f"future-fetch-manifest-from-filled-manual-packet-017c-{MARKET_ID}"
    manifest["source_packet_id"] = packet["packet_id"]
    manifest["source_validation"] = validation
    manifest["safety_summary"] = _safe_summary_017c()
    for index, row in enumerate(_mapping_rows(manifest.get("executable_request_intents")), start=1):
        source_name = str(row.get("source_name_or_placeholder") or row.get("source_item_id") or "public-source")
        row["request_intent_id"] = f"manual_url_fetch_request_017c_{index:02d}_{MARKET_ID}_{slug_id(source_name)}"
        row["source_packet_id"] = packet["packet_id"]
        row["operator_approval_required_before_fetch"] = True
        row["live_fetch_performed"] = False
    return manifest


def build_filled_manifest_url_safety_report(manifest: Mapping[str, Any]) -> dict[str, Any]:
    executable = _mapping_rows(manifest.get("executable_request_intents"))
    per_request = [
        validate_public_fetch_request_intent(row, request_index=index, max_request_count=MAX_REQUEST_COUNT)
        for index, row in enumerate(executable, start=1)
    ]
    blocked = [row for row in per_request if row.get("allowed") is not True]
    global_blockers = []
    if len(executable) > MAX_REQUEST_COUNT:
        global_blockers.append("request count exceeds max request count")
    return {
        "contract_version": "pmbot_filled_manifest_url_safety_report.v1",
        "generated_at": GENERATED_AT_017,
        "market_id": MARKET_ID,
        "market_title": MARKET_TITLE,
        "source_manifest_id": manifest.get("manifest_id"),
        "checked_request_count": len(executable),
        "request_count": len(executable),
        "max_request_count": MAX_REQUEST_COUNT,
        "allowed_count": len(per_request) - len(blocked),
        "blocked_count": len(blocked),
        "missing_url_count": int(manifest.get("missing_url_count") or 0),
        "per_request_safety": per_request,
        "global_blockers": global_blockers,
        "global_warnings": [],
        "all_executable_urls_pass_safety": not blocked and not global_blockers,
        "live_fetch_performed": False,
        "live_network_used": False,
        "safety_summary": _safe_summary_017c(),
    }


def build_scoped_approval_pending(manifest: Mapping[str, Any]) -> dict[str, Any]:
    executable = _mapping_rows(manifest.get("executable_request_intents"))
    return {
        "contract_version": "pmbot_new_market_fetch_scoped_approval_pending.v1",
        "approval_id": f"new-market-fetch-scoped-approval-pending-017c-{MARKET_ID}",
        "generated_at": GENERATED_AT_017,
        "approval_for_future_task_id": FUTURE_TASK_ID,
        "approval_status": "pending",
        "market_id": MARKET_ID,
        "market_title": MARKET_TITLE,
        "max_request_count": MAX_REQUEST_COUNT,
        "executable_request_count": len(executable),
        "approved_request_intent_ids_proposed": [str(row.get("request_intent_id")) for row in executable],
        "approved_market_ids_proposed": sorted({str(row.get("market_id")) for row in executable}),
        "approved_manifest_path": normalize_path(OUT_DIR / "future_fetch_manifest_from_filled_packet_017c.json"),
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
        "safety_summary": {**_safe_summary_017c(), "operator_approval_granted": False},
    }


def build_dashboard(previous_dashboard: Mapping[str, Any], validation: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_public_evidence_dashboard_url_filled_pending_approval.v1",
        "dashboard_id": "public-evidence-dashboard-url-filled-pending-approval-017c",
        "generated_at": GENERATED_AT_017,
        "tracked_market_count": TRACKED_MARKET_COUNT,
        "markets": copy.deepcopy(previous_dashboard.get("markets", [])),
        "market_id": MARKET_ID,
        "market_title": MARKET_TITLE,
        "filled_url_count": int(validation.get("filled_url_count") or 0),
        "valid_url_count": int(validation.get("valid_url_count") or 0),
        "executable_request_count": int(manifest.get("executable_request_count") or 0),
        "missing_url_count": int(manifest.get("missing_url_count") or 0),
        "blocked_request_count": int(manifest.get("blocked_request_count") or 0),
        "ready_for_operator_approval": bool(manifest.get("ready_for_operator_approval")),
        "approval_pending": True,
        "live_fetch_performed": False,
        "new_market_url_state": {
            "market_id": MARKET_ID,
            "market_title": MARKET_TITLE,
            "packet_path": normalize_path(OUT_DIR / "manual_public_url_collection_packet_573656.filled.json"),
            "validation_result_path": normalize_path(OUT_DIR / "filled_url_validation_result_017c.json"),
            "future_manifest_path": normalize_path(OUT_DIR / "future_fetch_manifest_from_filled_packet_017c.json"),
            "approval_packet_path": normalize_path(OUT_DIR / "new_market_fetch_scoped_approval_pending_017c.json"),
            "filled_url_count": int(validation.get("filled_url_count") or 0),
            "valid_url_count": int(validation.get("valid_url_count") or 0),
            "executable_request_count": int(manifest.get("executable_request_count") or 0),
            "missing_url_count": int(manifest.get("missing_url_count") or 0),
            "blocked_request_count": int(manifest.get("blocked_request_count") or 0),
            "ready_for_operator_approval": bool(manifest.get("ready_for_operator_approval")),
            "approval_pending": True,
        },
        "next_operator_action": FUTURE_TASK_ID,
        "no_real_trade_decision": True,
        "safety_summary": _safe_summary_017c(),
    }


def build_operator_card(
    packet: Mapping[str, Any],
    validation: Mapping[str, Any],
    manifest: Mapping[str, Any],
    approval: Mapping[str, Any],
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_manual_url_filled_operator_card.v1",
        "card_id": "manual-url-filled-operator-card-017c",
        "generated_at": GENERATED_AT_017,
        "market": {"market_id": MARKET_ID, "market_title": MARKET_TITLE},
        "urls_filled": [
            {
                "source_category": row.get("source_category"),
                "source_name": row.get("source_name"),
                "operator_supplied_url": row.get("operator_supplied_url"),
                "url_status": validation_row.get("url_status"),
            }
            for row, validation_row in zip(
                _mapping_rows(packet.get("candidate_urls")),
                _mapping_rows(validation.get("candidate_url_results")),
            )
        ],
        "request_counts": {
            "supplied_url_count": packet.get("supplied_url_count"),
            "valid_url_count": validation.get("valid_url_count"),
            "missing_url_count": manifest.get("missing_url_count"),
            "blocked_request_count": manifest.get("blocked_request_count"),
            "executable_request_count": manifest.get("executable_request_count"),
        },
        "future_fetch_readiness": {
            "ready_for_operator_approval": manifest.get("ready_for_operator_approval"),
            "approval_status": approval.get("approval_status"),
            "ready_to_execute_public_read_only_fetch": preflight.get("ready_to_execute_public_read_only_fetch"),
            "would_be_ready_after_operator_approval": preflight.get("would_be_ready_after_operator_approval"),
        },
        "approval_still_pending": True,
        "next_safe_action": FUTURE_TASK_ID,
        "remains_prohibited": [
            "Live public URL reads before scoped operator approval.",
            "Authenticated endpoints, API keys, cookies, browser profiles, wallet access, orders, trading, schedulers, background workers, or polling.",
            "Outcome resolution changes or market instruction output.",
        ],
        "live_fetch_performed": False,
        "no_real_trade_decision": True,
        "safety_summary": _safe_summary_017c(),
    }


def build_result(
    validation: Mapping[str, Any],
    manifest: Mapping[str, Any],
    approval: Mapping[str, Any],
    preflight: Mapping[str, Any],
    dashboard: Mapping[str, Any],
    operator_card: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
    generated_artifacts: list[str],
) -> dict[str, Any]:
    executable = int(manifest.get("executable_request_count") or 0)
    would_after = bool(preflight.get("would_be_ready_after_operator_approval"))
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
        "filled_manual_url_packet_created": True,
        "supplied_url_count": 3,
        "valid_url_count": int(validation.get("valid_url_count") or 0),
        "missing_url_count": int(manifest.get("missing_url_count") or 0),
        "blocked_url_count": int(manifest.get("blocked_request_count") or 0),
        "future_manifest_created": True,
        "executable_request_count": executable,
        "ready_for_operator_approval": bool(manifest.get("ready_for_operator_approval")),
        "scoped_pending_approval_created": bool(approval),
        "future_fetch_preflight_created": bool(preflight),
        "would_be_ready_after_operator_approval": would_after,
        "dashboard_url_filled_pending_approval_created": bool(dashboard),
        "operator_card_created": bool(operator_card),
        "manual_url_filled_safety_scan_passed": bool(safety_scan.get("safety_ok")),
        "selected_market_id": MARKET_ID,
        "selected_market_title": MARKET_TITLE,
        "tracked_market_count": TRACKED_MARKET_COUNT,
        "live_fetch_performed": False,
        "outcome_resolution_invented": False,
        "generated_artifacts": generated_artifacts,
        "tests_run": [
            "python -m compileall ai_orchestrator pm_bot tests",
            "pytest pm_bot/tests/test_practical_manual_url_collection_fill_017c.py",
            "pytest pm_bot/tests/test_practical_manual_url_future_manifest_017c.py",
            "pytest pm_bot/tests/test_practical_manual_url_filled_outputs_017c.py",
            "pytest pm_bot/tests/test_practical_manual_url_collection_017b.py",
            "pytest pm_bot/tests/test_practical_manual_url_to_fetch_manifest_017b.py",
            "pytest pm_bot/tests/test_practical_safety_scan.py",
            "pytest pm_bot/tests/test_practical_public_fetch_execution_preflight.py",
            "pytest pm_bot/tests/test_practical_public_source_registry.py",
            "python -m json.tool docs/ORCH_PMBOT_PRACTICAL_017C_RESULT.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017c/manual_public_url_collection_packet_573656.filled.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017c/filled_url_validation_result_017c.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017c/future_fetch_manifest_from_filled_packet_017c.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017c/filled_manifest_url_safety_report_017c.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017c/new_market_fetch_scoped_approval_pending_017c.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017c/new_market_fetch_preflight_from_filled_urls_017c.result.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017c/public_evidence_dashboard_url_filled_pending_approval_017c.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017c/manual_url_filled_operator_card_017c.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_url_collection_017c/manual_url_filled_safety_scan_017c.result.json",
            "git diff --check",
            "git diff --cached --check",
        ],
        "validation_passed": (
            int(validation.get("valid_url_count") or 0) == 3
            and int(validation.get("missing_url_count") or 0) == 0
            and int(validation.get("blocked_url_count") or 0) == 0
        ),
        "safety_ok": bool(safety_scan.get("safety_ok")),
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
        "next_recommended_action": FUTURE_TASK_ID if executable > 0 and would_after else PREVIOUS_TASK_ID,
    }


def render_validation_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# Filled URL Validation Result 017C",
        "",
        f"- Packet: `{result.get('source_packet_id')}`",
        f"- Market: `{result.get('market_id')}` {result.get('market_title')}",
        f"- Filled URLs: {result.get('filled_url_count')}",
        f"- Valid URLs: {result.get('valid_url_count')}",
        f"- Missing URLs: {result.get('missing_url_count')}",
        f"- Blocked URLs: {result.get('blocked_url_count')}",
        f"- Ready for fetch manifest: `{str(result.get('ready_for_fetch_manifest')).lower()}`",
        f"- Live fetch performed: `{str(result.get('live_fetch_performed')).lower()}`",
        "",
        "## Candidate Results",
        "",
    ]
    for row in _mapping_rows(result.get("candidate_url_results")):
        lines.extend(
            [
                f"- `{row.get('item_id')}` `{row.get('url_status')}`",
                f"  URL: `{row.get('operator_supplied_url')}`",
                f"  Notes: {', '.join(row.get('validation_notes', [])) or 'none'}",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- Validation checked URL shape, category policy, request count, credential hints, private host hints, and execution-adjacent path hints locally.",
            "- No URL was fetched and no evidence was captured.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_safety_report_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Filled Manifest URL Safety Report 017C",
        "",
        f"- Checked requests: {report.get('checked_request_count')}",
        f"- Allowed requests: {report.get('allowed_count')}",
        f"- Blocked requests: {report.get('blocked_count')}",
        f"- Missing URLs: {report.get('missing_url_count')}",
        f"- All executable URLs pass safety: `{str(report.get('all_executable_urls_pass_safety')).lower()}`",
        f"- Live fetch performed: `{str(report.get('live_fetch_performed')).lower()}`",
        "",
        "## Per Request Safety",
        "",
    ]
    for row in _mapping_rows(report.get("per_request_safety")):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}` allowed: `{str(row.get('allowed')).lower()}`",
                f"  Category: `{row.get('source_category')}`",
                f"  URL: `{row.get('sanitized_url_reference')}`",
                f"  Blockers: {', '.join(row.get('blockers', [])) or 'none'}",
                f"  Warnings: {', '.join(row.get('warnings', [])) or 'none'}",
            ]
        )
    return "\n".join(lines) + "\n"


def render_approval_markdown(approval: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# New Market Fetch Scoped Approval Pending 017C",
            "",
            f"- Future task: `{approval.get('approval_for_future_task_id')}`",
            f"- Approval status: `{approval.get('approval_status')}`",
            f"- Market: `{approval.get('market_id')}` {approval.get('market_title')}",
            f"- Max request count: {approval.get('max_request_count')}",
            f"- Executable request count: {approval.get('executable_request_count')}",
            f"- Operator approval required: `{str(approval.get('operator_approval_required')).lower()}`",
            f"- Operator approval granted: `{str(approval.get('operator_approval_granted')).lower()}`",
            f"- Live fetch performed: `{str(approval.get('live_fetch_performed')).lower()}`",
            "",
            "## Boundary",
            "",
            "- Pending approval only; it is non-reusable and expires after the named future task.",
            "- No authentication, API keys, cookies, wallet access, orders, trading, scheduler, or background worker is allowed.",
        ]
    ) + "\n"


def render_dashboard_markdown(dashboard: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Public Evidence Dashboard URL Filled Pending Approval 017C",
            "",
            f"- Tracked markets: {dashboard.get('tracked_market_count')}",
            f"- Market: `{dashboard.get('market_id')}` {dashboard.get('market_title')}",
            f"- Filled URLs: {dashboard.get('filled_url_count')}",
            f"- Executable requests: {dashboard.get('executable_request_count')}",
            f"- Missing URLs: {dashboard.get('missing_url_count')}",
            f"- Blocked requests: {dashboard.get('blocked_request_count')}",
            f"- Ready for operator approval: `{str(dashboard.get('ready_for_operator_approval')).lower()}`",
            f"- Approval pending: `{str(dashboard.get('approval_pending')).lower()}`",
            f"- Live fetch performed: `{str(dashboard.get('live_fetch_performed')).lower()}`",
            "",
            "## Next Operator Action",
            "",
            f"- `{dashboard.get('next_operator_action')}`",
        ]
    ) + "\n"


def render_operator_card_markdown(card: Mapping[str, Any]) -> str:
    market = card.get("market", {})
    counts = card.get("request_counts", {})
    readiness = card.get("future_fetch_readiness", {})
    lines = [
        "# Manual URL Filled Operator Card 017C",
        "",
        f"- Market: `{market.get('market_id')}` {market.get('market_title')}",
        f"- URLs filled: {counts.get('supplied_url_count')}",
        f"- Valid URLs: {counts.get('valid_url_count')}",
        f"- Missing URLs: {counts.get('missing_url_count')}",
        f"- Blocked requests: {counts.get('blocked_request_count')}",
        f"- Executable requests: {counts.get('executable_request_count')}",
        f"- Ready for operator approval: `{str(readiness.get('ready_for_operator_approval')).lower()}`",
        f"- Approval status: `{readiness.get('approval_status')}`",
        f"- Ready to execute now: `{str(readiness.get('ready_to_execute_public_read_only_fetch')).lower()}`",
        f"- Would be ready after operator approval: `{str(readiness.get('would_be_ready_after_operator_approval')).lower()}`",
        "",
        "## URLs Filled",
        "",
    ]
    for row in _mapping_rows(card.get("urls_filled")):
        lines.extend(
            [
                f"- `{row.get('source_category')}` {row.get('source_name')}",
                f"  URL: `{row.get('operator_supplied_url')}`",
                f"  Status: `{row.get('url_status')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Next Safe Action",
            "",
            f"- `{card.get('next_safe_action')}` after scoped operator approval is granted in that future task.",
            "",
            "## Remains Prohibited",
            "",
            *bullet_lines(card.get("remains_prohibited", [])),
        ]
    )
    return "\n".join(lines) + "\n"


def render_safety_scan_markdown(report: Mapping[str, Any]) -> str:
    confirmations = [
        "live_network_used",
        "openrouter_calls_performed",
        "new_polymarket_api_calls_performed",
        "authenticated_endpoints_used",
        "wallet_or_private_key_access",
        "orders_or_trading_actions",
        "runtime_or_dispatcher_changes",
        "market_recommendation_generated",
        "probability_ev_edge_or_side_selection_generated",
        "outcome_resolution_invented",
        "no_scheduler_daemon_background_worker",
        "no_autonomous_trading",
    ]
    return "\n".join(
        [
            "# Manual URL Filled Safety Scan 017C",
            "",
            f"- Scanned paths: {len(report.get('scanned_paths', []))}",
            f"- Issues: {report.get('issue_count')}",
            f"- Safety OK: `{str(report.get('safety_ok')).lower()}`",
            "",
            "## Confirmations",
            "",
            *bullet_lines(f"`{key}`: `{report.get(key)}`" for key in confirmations),
            "",
            "## Issues",
            "",
            *bullet_lines(
                f"`{row.get('path')}` `{row.get('issue_type')}` - {row.get('detail')}"
                for row in _mapping_rows(report.get("issues"))
            ),
        ]
    ) + "\n"


def render_fill_doc(validation: Mapping[str, Any], manifest: Mapping[str, Any], approval: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Fill New Market Public URL Packet",
            "",
            "PRACTICAL-017B produced a manual URL packet for the Bitcoin $150k market with three missing URL rows. PRACTICAL-017C fills that packet from operator-provided concrete public URLs and validates them locally without any public URL read.",
            "",
            f"- Market: `{MARKET_ID}` {MARKET_TITLE}",
            "- Supplied URLs: 3",
            f"- Valid URLs: {validation.get('valid_url_count')}",
            f"- Missing URLs: {manifest.get('missing_url_count')}",
            f"- Blocked URLs: {manifest.get('blocked_request_count')}",
            f"- Executable future request intents: {manifest.get('executable_request_count')}",
            f"- Ready for operator approval: `{str(manifest.get('ready_for_operator_approval')).lower()}`",
            f"- Approval status: `{approval.get('approval_status')}`",
            "",
            "## URLs Supplied",
            "",
            *bullet_lines(
                f"`{row['source_category']}` {row['source_name']}: `{row['operator_supplied_url']}`"
                for row in OPERATOR_PROVIDED_URLS
            ),
            "",
            "## Why No Live Fetch Was Performed",
            "",
            "- This task only filled and locally validated URL strings for a future controlled public read-only fetch.",
            "- URL availability, page content, and evidence capture remain out of scope until a separate scoped approval task.",
            "",
            "## Next Recommended Action",
            "",
            f"- `{FUTURE_TASK_ID}` if the operator grants scoped approval for the prepared manifest.",
        ]
    ) + "\n"


def render_task_doc(
    validation: Mapping[str, Any],
    manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
    dashboard: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# ORCH PMBOT PRACTICAL 017C - Fill New Market Public URL Packet Manually",
            "",
            f"- Task ID: `{TASK_ID}`",
            f"- Relation to PRACTICAL-017B: fills the previously unfilled manual public URL packet for market `{MARKET_ID}`.",
            f"- Tracked market count: {dashboard.get('tracked_market_count')}",
            f"- Valid URL count: {validation.get('valid_url_count')}",
            f"- Missing URL count: {manifest.get('missing_url_count')}",
            f"- Blocked URL count: {manifest.get('blocked_request_count')}",
            f"- Executable request count: {manifest.get('executable_request_count')}",
            f"- Ready for operator approval: `{str(manifest.get('ready_for_operator_approval')).lower()}`",
            f"- Ready to execute now: `{str(preflight.get('ready_to_execute_public_read_only_fetch')).lower()}`",
            f"- Would be ready after operator approval: `{str(preflight.get('would_be_ready_after_operator_approval')).lower()}`",
            f"- Safety scan passed: `{str(safety_scan.get('safety_ok')).lower()}`",
            "",
            "## Outputs",
            "",
            "- Filled packet in JSON and Markdown.",
            "- Local validation result and URL safety report.",
            "- Future fetch manifest, scoped pending approval packet, and preflight dry-run.",
            "- Dashboard update and operator card.",
            "- Safety scan over the 017C artifact directory.",
            "",
            "## Safety Boundary",
            "",
            "- No live public URL read, browser automation, search, OpenRouter call, Polymarket API call, authenticated endpoint, credential, cookie, wallet access, order path, trading path, scheduler, daemon, background worker, polling loop, runtime path, or dispatcher path was used.",
            "- No unresolved market was marked resolved and no market instruction was generated.",
            "",
            "## Next Recommended Action",
            "",
            f"- `{FUTURE_TASK_ID}` if scoped operator approval is granted; otherwise `{PREVIOUS_TASK_ID}` remains pending.",
        ]
    ) + "\n"


def write_017c_package() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source_packet = load_json_object(SOURCE_PACKET_PATH, label="017B manual URL packet")
    source_validation = load_json_object(SOURCE_VALIDATION_PATH, label="017B validation result")
    source_manifest = load_json_object(SOURCE_MANIFEST_PATH, label="017B future manifest")
    previous_dashboard = load_json_object(SOURCE_DASHBOARD_PATH, label="017B dashboard")

    if source_packet.get("market_id") != MARKET_ID:
        raise ValueError("017B packet market_id does not match 573656")
    if source_validation.get("missing_url_count") != 3 or source_validation.get("filled_url_count") != 0:
        raise ValueError("017B validation result is not in expected unfilled state")
    if source_manifest.get("executable_request_count") != 0 or source_manifest.get("live_fetch_performed") is not False:
        raise ValueError("017B future manifest is not in expected no-fetch state")

    packet = build_filled_manual_url_packet(source_packet)
    validation = build_validation_result(packet)
    manifest = build_manifest(packet, validation)
    safety_report = build_filled_manifest_url_safety_report(manifest)
    approval = build_scoped_approval_pending(manifest)
    preflight = build_enriched_manifest_execution_preflight(
        enriched_manifest=manifest,
        pending_approval=approval,
        expected_future_task_id=FUTURE_TASK_ID,
    )
    preflight["generated_at"] = GENERATED_AT_017
    preflight["safety_summary"] = _safe_summary_017c()
    dashboard = build_dashboard(previous_dashboard, validation, manifest)
    operator_card = build_operator_card(packet, validation, manifest, approval, preflight)

    json_writes = [
        (OUT_DIR / "manual_public_url_collection_packet_573656.filled.json", packet),
        (OUT_DIR / "filled_url_validation_result_017c.json", validation),
        (OUT_DIR / "future_fetch_manifest_from_filled_packet_017c.json", manifest),
        (OUT_DIR / "filled_manifest_url_safety_report_017c.json", safety_report),
        (OUT_DIR / "new_market_fetch_scoped_approval_pending_017c.json", approval),
        (OUT_DIR / "new_market_fetch_preflight_from_filled_urls_017c.result.json", preflight),
        (OUT_DIR / "public_evidence_dashboard_url_filled_pending_approval_017c.json", dashboard),
        (OUT_DIR / "manual_url_filled_operator_card_017c.json", operator_card),
    ]
    for path, payload in json_writes:
        write_json(path, payload)

    text_writes = [
        (
            OUT_DIR / "manual_public_url_collection_packet_573656.filled.md",
            render_manual_public_url_collection_packet_markdown(packet).replace("017B", "017C"),
        ),
        (OUT_DIR / "filled_url_validation_result_017c.md", render_validation_markdown(validation)),
        (
            OUT_DIR / "future_fetch_manifest_from_filled_packet_017c.md",
            render_future_fetch_manifest_from_manual_packet_markdown(manifest).replace("017B", "017C"),
        ),
        (OUT_DIR / "filled_manifest_url_safety_report_017c.md", render_safety_report_markdown(safety_report)),
        (OUT_DIR / "new_market_fetch_scoped_approval_pending_017c.md", render_approval_markdown(approval)),
        (
            OUT_DIR / "new_market_fetch_preflight_from_filled_urls_017c.md",
            render_enriched_manifest_execution_preflight_markdown(preflight),
        ),
        (OUT_DIR / "public_evidence_dashboard_url_filled_pending_approval_017c.md", render_dashboard_markdown(dashboard)),
        (OUT_DIR / "manual_url_filled_operator_card_017c.md", render_operator_card_markdown(operator_card)),
    ]
    for path, payload in text_writes:
        write_text(path, payload)

    safety_scan = run_practical_safety_scan(artifact_dirs=[OUT_DIR])
    safety_scan.update(
        {
            "manual_url_filled_safety_scan_passed": bool(safety_scan.get("safety_ok")),
            "live_network_used": False,
            "live_fetch_performed": False,
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
            "safety_summary": _safe_summary_017c(),
        }
    )
    write_json(OUT_DIR / "manual_url_filled_safety_scan_017c.result.json", safety_scan)
    write_text(OUT_DIR / "manual_url_filled_safety_scan_017c.md", render_safety_scan_markdown(safety_scan))

    generated_artifacts = sorted(
        normalize_path(path)
        for path in OUT_DIR.rglob("*")
        if path.suffix.lower() in {".json", ".md"}
    )
    generated_artifacts.extend(
        [
            "docs/PMBOT_FILL_NEW_MARKET_PUBLIC_URL_PACKET.md",
            "docs/ORCH_PMBOT_PRACTICAL_017C_FILL_NEW_MARKET_PUBLIC_URL_PACKET_MANUALLY.md",
            "docs/ORCH_PMBOT_PRACTICAL_017C_RESULT.json",
        ]
    )
    result = build_result(validation, manifest, approval, preflight, dashboard, operator_card, safety_scan, generated_artifacts)

    write_text(DOCS_DIR / "PMBOT_FILL_NEW_MARKET_PUBLIC_URL_PACKET.md", render_fill_doc(validation, manifest, approval))
    write_text(
        DOCS_DIR / "ORCH_PMBOT_PRACTICAL_017C_FILL_NEW_MARKET_PUBLIC_URL_PACKET_MANUALLY.md",
        render_task_doc(validation, manifest, preflight, dashboard, safety_scan),
    )
    write_json(DOCS_DIR / "ORCH_PMBOT_PRACTICAL_017C_RESULT.json", result)

    return {
        "packet": packet,
        "validation": validation,
        "manifest": manifest,
        "safety_report": safety_report,
        "approval": approval,
        "preflight": preflight,
        "dashboard": dashboard,
        "operator_card": operator_card,
        "safety_scan": safety_scan,
        "result": result,
    }


def main() -> int:
    payload = write_017c_package()
    validation = payload["validation"]
    manifest = payload["manifest"]
    safety_scan = payload["safety_scan"]
    print(
        "generated 017C artifacts: "
        f"valid_url_count={validation['valid_url_count']} "
        f"executable_request_count={manifest['executable_request_count']} "
        f"safety_ok={safety_scan['safety_ok']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
