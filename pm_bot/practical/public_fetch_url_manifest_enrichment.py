from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text
from pm_bot.practical.practical_safety_scan import render_practical_safety_scan_markdown, run_practical_safety_scan
from pm_bot.practical.public_fetch_url_safety import validate_public_fetch_request_intent
from pm_bot.practical.public_source_registry import validate_source_category

ENRICHED_MANIFEST_CONTRACT_VERSION = "pmbot_enriched_public_fetch_request_manifest.v1"
URL_SAFETY_REPORT_CONTRACT_VERSION = "pmbot_enriched_public_fetch_url_safety_report.v1"
PENDING_APPROVAL_CONTRACT_VERSION = "pmbot_enriched_public_fetch_scoped_approval_pending.v1"
OPERATOR_CARD_CONTRACT_VERSION = "pmbot_concrete_url_manifest_operator_card.v1"
SOURCE_TASK_ID = "ORCH-PMBOT-PRACTICAL-007-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-OPERATOR-APPROVED"
ENRICHMENT_TASK_ID = "ORCH-PMBOT-PRACTICAL-007B-ENRICH-PUBLIC-SOURCE-URL-MANIFEST-LOCAL-ONLY"
FUTURE_FETCH_TASK_ID = "ORCH-PMBOT-PRACTICAL-008-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-WITH-CONCRETE-URL-MANIFEST"

CATEGORY_PRIORITY = {
    "public_court_government_page_placeholder": 10,
    "public_resolution_source_page_placeholder": 20,
    "public_exchange_company_announcement_page_placeholder": 30,
    "public_issuer_company_news_page_placeholder": 40,
    "public_market_metadata_endpoint_placeholder": 50,
    "public_static_web_page_placeholder": 60,
    "low_quality_forum_or_rumor_labeled_source": 90,
}


def build_enriched_fetch_request_manifest(
    *,
    original_manifest: Mapping[str, Any],
    source_registry: Mapping[str, Any] | None = None,
    source_dependency_map: Mapping[str, Any] | None = None,
    normalized_market_inputs: Sequence[Mapping[str, Any]] = (),
    manual_url_mapping_fixture: Mapping[str, Any] | None = None,
    max_request_count: int = 5,
    fixture_mode: bool = False,
) -> dict[str, Any]:
    """Promote only locally curated safe public URLs into executable intents."""

    del source_registry  # The authoritative category validator is imported locally.
    source_dependency_map = source_dependency_map or {}
    fixture_rows = _fixture_rows(manual_url_mapping_fixture or {})
    context_by_market = _market_context_by_id(normalized_market_inputs)
    dependency_ids_by_market = _dependency_ids_by_market(source_dependency_map)
    request_intents = [intent for intent in original_manifest.get("request_intents", []) if isinstance(intent, Mapping)]

    safe_candidates: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    warnings: list[str] = []

    for original_index, intent in enumerate(request_intents, start=1):
        market_id = clean_text(intent.get("market_id"))
        fixture_row = _matching_fixture_row(fixture_rows, intent)
        candidate_url = _candidate_url(intent, fixture_row)
        fixture_status = clean_text(fixture_row.get("url_status") if fixture_row else "")
        fixture_reason = clean_text(fixture_row.get("reason") if fixture_row else "")
        source_category = clean_text(intent.get("source_category"))
        category_validation = validate_source_category(source_category)

        if fixture_status == "blocked":
            blocked.append(
                _blocked_row(
                    intent,
                    reason=fixture_reason or "manual fixture marked this source as blocked",
                    original_index=original_index,
                    safety_blockers=[],
                    blocked_url_present=bool(candidate_url),
                )
            )
            continue
        if category_validation["blocked"]:
            blocked.append(
                _blocked_row(
                    intent,
                    reason=category_validation["reason"],
                    original_index=original_index,
                    safety_blockers=[category_validation["reason"]],
                    blocked_url_present=bool(candidate_url),
                )
            )
            continue
        if not candidate_url:
            missing.append(
                _missing_row(
                    intent,
                    reason=fixture_reason or "no concrete public HTTP(S) URL is available in local artifacts or fixture",
                    original_index=original_index,
                    dependency_source_ids=dependency_ids_by_market.get(market_id, []),
                    normalized_source_reference_count=context_by_market.get(market_id, {}).get("source_reference_count", 0),
                )
            )
            continue

        candidate_intent = _executable_candidate_intent(
            intent=intent,
            candidate_url=candidate_url,
            original_index=original_index,
            fixture_row=fixture_row,
        )
        safety = validate_public_fetch_request_intent(
            candidate_intent,
            request_index=1,
            max_request_count=max_request_count,
            fixture_mode=fixture_mode,
        )
        if safety["allowed"]:
            candidate_intent["url_safety_validation"] = {
                "allowed": True,
                "warnings": safety.get("warnings", []),
            }
            safe_candidates.append(candidate_intent)
        else:
            blocked.append(
                _blocked_row(
                    intent,
                    reason="concrete URL candidate failed local URL safety validation",
                    original_index=original_index,
                    safety_blockers=safety.get("blockers", []),
                    blocked_url_present=True,
                )
            )

    selected, omitted = _cap_safe_candidates(safe_candidates, max_request_count=max_request_count)
    if missing:
        warnings.append(f"{len(missing)} placeholder request intents still lack concrete public URLs.")
    if blocked:
        warnings.append(f"{len(blocked)} request intents are blocked and remain non-executable.")
    if omitted:
        warnings.append(f"{len(omitted)} safe URL candidates were omitted to keep the request count within {max_request_count}.")

    blockers: list[str] = []
    if not selected:
        blockers.append("no concrete safe public URLs")
    within_request_limit = len(selected) <= max_request_count
    if not within_request_limit:
        blockers.append("executable request count exceeds max request count")

    return {
        "contract_version": ENRICHED_MANIFEST_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "source_task_id": SOURCE_TASK_ID,
        "enrichment_task_id": ENRICHMENT_TASK_ID,
        "source_manifest_id": clean_text(original_manifest.get("request_manifest_id")),
        "source_manifest_contract_version": clean_text(original_manifest.get("contract_version")),
        "market_ids": list(original_manifest.get("market_ids", [])),
        "request_count_total": len(request_intents),
        "original_request_count": len(request_intents),
        "max_request_count": max_request_count,
        "executable_request_intents": selected,
        "missing_url_request_intents": missing,
        "blocked_request_intents": blocked,
        "omitted_safe_candidates": omitted,
        "executable_request_count": len(selected),
        "missing_url_count": len(missing),
        "blocked_request_count": len(blocked),
        "omitted_safe_candidate_count": len(omitted),
        "within_request_limit": within_request_limit,
        "live_fetch_performed": False,
        "ready_for_future_controlled_fetch_attempt": bool(selected) and within_request_limit,
        "blockers": blockers,
        "warnings": warnings,
        "selection_policy": {
            "max_request_count": max_request_count,
            "deterministic_order": "source category priority, then original manifest order, then market_id, then request_intent_id",
            "concrete_url_policy": "Only executable_request_intents contain concrete HTTP(S) URLs.",
            "missing_policy": "Placeholder-only source references stay non-executable.",
            "blocked_policy": "Auth, wallet, order, trading, credential, cookie, login, and unsafe URL shapes stay non-executable.",
        },
        "safety_summary": safe_summary(),
    }


def render_enriched_fetch_request_manifest_markdown(manifest: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Enriched Public Fetch Request Manifest",
        "",
        f"- Source task: `{manifest.get('source_task_id')}`",
        f"- Enrichment task: `{manifest.get('enrichment_task_id')}`",
        f"- Original request intents: {manifest.get('original_request_count')}",
        f"- Executable request intents: {manifest.get('executable_request_count')}",
        f"- Missing URL intents: {manifest.get('missing_url_count')}",
        f"- Blocked intents: {manifest.get('blocked_request_count')}",
        f"- Max requests: {manifest.get('max_request_count')}",
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
                f"  Market: `{row.get('market_id')}` {row.get('market_title')}",
                f"  Source category: `{row.get('source_category')}`",
                f"  Concrete public URL: `{row.get('source_url')}`",
                f"  Reason: {row.get('url_selection_reason')}",
            ]
        )
    lines.extend(["", "## Missing URL Request Intents", ""])
    for row in manifest.get("missing_url_request_intents", []):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}`",
                f"  Market: `{row.get('market_id')}` {row.get('market_title')}",
                f"  Source category: `{row.get('source_category')}`",
                f"  Reason: {row.get('missing_url_reason')}",
            ]
        )
    lines.extend(["", "## Blocked Request Intents", ""])
    for row in manifest.get("blocked_request_intents", []):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}`",
                f"  Market: `{row.get('market_id')}` {row.get('market_title')}",
                f"  Source category: `{row.get('source_category')}`",
                f"  Reason: {row.get('blocked_reason')}",
            ]
        )
    lines.extend(
        [
            "",
            "## Omitted Safe Candidates",
            "",
            *bullet_lines(
                f"`{row.get('request_intent_id')}` market `{row.get('market_id')}` - {row.get('omitted_reason')}"
                for row in manifest.get("omitted_safe_candidates", [])
            ),
            "",
            "## Blockers",
            "",
            *bullet_lines(manifest.get("blockers", [])),
            "",
            "## Warnings",
            "",
            *bullet_lines(manifest.get("warnings", [])),
            "",
            "## Safety Boundary",
            "",
            "- This artifact is local-only manifest preparation.",
            "- No URL was fetched while creating this package.",
            "- Non-executable missing, blocked, and omitted entries do not carry concrete HTTP(S) URLs.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_enriched_manifest_url_safety_report(
    *,
    enriched_manifest: Mapping[str, Any],
    fixture_mode: bool = False,
) -> dict[str, Any]:
    max_request_count = int(enriched_manifest.get("max_request_count") or 5)
    executable = [row for row in enriched_manifest.get("executable_request_intents", []) if isinstance(row, Mapping)]
    per_request = [
        validate_public_fetch_request_intent(
            row,
            request_index=index,
            max_request_count=max_request_count,
            fixture_mode=fixture_mode,
        )
        for index, row in enumerate(executable, start=1)
    ]
    unsafe_executable_count = sum(1 for row in per_request if row.get("allowed") is not True)
    global_blockers: list[str] = []
    if len(executable) > max_request_count:
        global_blockers.append("executable request count exceeds max request count")
    if unsafe_executable_count:
        global_blockers.append("one or more executable URL candidates failed local safety validation")
    global_warnings: list[str] = []
    missing_count = int(enriched_manifest.get("missing_url_count") or 0)
    manifest_blocked_count = int(enriched_manifest.get("blocked_request_count") or 0)
    if missing_count:
        global_warnings.append(f"{missing_count} request intents are missing concrete URLs and are non-executable.")
    if manifest_blocked_count:
        global_warnings.append(f"{manifest_blocked_count} request intents are blocked and are non-executable.")
    return {
        "contract_version": URL_SAFETY_REPORT_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "checked_request_count": len(executable),
        "allowed_count": sum(1 for row in per_request if row.get("allowed") is True),
        "blocked_count": manifest_blocked_count + unsafe_executable_count,
        "missing_url_count": missing_count,
        "per_request_safety": per_request,
        "global_blockers": global_blockers,
        "global_warnings": global_warnings,
        "live_fetch_performed": False,
        "safety_summary": safe_summary(),
    }


def render_enriched_manifest_url_safety_report_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Enriched Manifest URL Safety Report",
        "",
        f"- Checked executable requests: {report.get('checked_request_count')}",
        f"- Allowed executable URLs: {report.get('allowed_count')}",
        f"- Blocked/non-executable count: {report.get('blocked_count')}",
        f"- Missing URL count: {report.get('missing_url_count')}",
        f"- Live fetch performed: `{str(report.get('live_fetch_performed')).lower()}`",
        "",
        "## Per Request Safety",
        "",
    ]
    for row in report.get("per_request_safety", []):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}` allowed: `{str(row.get('allowed')).lower()}`",
                f"  Market: `{row.get('market_id')}`",
                f"  URL: `{row.get('sanitized_url_reference')}`",
                f"  Blockers: {', '.join(row.get('blockers', [])) or 'none'}",
                f"  Warnings: {', '.join(row.get('warnings', [])) or 'none'}",
            ]
        )
    lines.extend(
        [
            "",
            "## Global Blockers",
            "",
            *bullet_lines(report.get("global_blockers", [])),
            "",
            "## Global Warnings",
            "",
            *bullet_lines(report.get("global_warnings", [])),
            "",
            "## Safety Boundary",
            "",
            "- URL safety validation is local and happens before any request.",
            "- This report did not perform a network fetch.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_scoped_approval_for_enriched_manifest(enriched_manifest: Mapping[str, Any]) -> dict[str, Any]:
    executable = [row for row in enriched_manifest.get("executable_request_intents", []) if isinstance(row, Mapping)]
    return {
        "contract_version": PENDING_APPROVAL_CONTRACT_VERSION,
        "approval_id": "scoped-approval-for-enriched-public-fetch-manifest-007b",
        "approval_status": "pending",
        "approval_for_future_task_id": FUTURE_FETCH_TASK_ID,
        "max_request_count": enriched_manifest.get("max_request_count", 5),
        "executable_request_count": len(executable),
        "approved_market_ids_proposed": sorted({clean_text(row.get("market_id")) for row in executable}),
        "approved_request_intent_ids_proposed": [clean_text(row.get("request_intent_id")) for row in executable],
        "operator_approval_required": True,
        "operator_approval_granted": False,
        "live_fetch_performed": False,
        "expires_after_future_task": True,
        "reusable": False,
        "blocked_scope": [
            "authenticated endpoints",
            "API keys, cookies, login, KYC, browser profiles, and bypass automation",
            "wallet, private key, signing, custody, order, or trading paths",
            "OpenRouter calls",
            "Polymarket API calls",
            "schedulers, daemons, watchers, automatic polling, and unattended automation",
            "market recommendations or executable quantitative market output",
        ],
        "safety_summary": {**safe_summary(), "operator_approval_granted": False, "live_fetch_performed": False},
    }


def render_scoped_approval_for_enriched_manifest_markdown(approval: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Scoped Approval For Enriched Manifest",
            "",
            f"- Approval status: `{approval.get('approval_status')}`",
            f"- Future task: `{approval.get('approval_for_future_task_id')}`",
            f"- Max requests: {approval.get('max_request_count')}",
            f"- Proposed executable requests: {approval.get('executable_request_count')}",
            f"- Operator approval required: `{str(approval.get('operator_approval_required')).lower()}`",
            f"- Operator approval granted: `{str(approval.get('operator_approval_granted')).lower()}`",
            f"- Live fetch performed: `{str(approval.get('live_fetch_performed')).lower()}`",
            "",
            "## Proposed Markets",
            "",
            *bullet_lines(f"`{market_id}`" for market_id in approval.get("approved_market_ids_proposed", [])),
            "",
            "## Proposed Request Intents",
            "",
            *bullet_lines(f"`{request_id}`" for request_id in approval.get("approved_request_intent_ids_proposed", [])),
            "",
            "## Blocked Scope",
            "",
            *bullet_lines(approval.get("blocked_scope", [])),
        ]
    ) + "\n"


def build_concrete_url_manifest_operator_card(
    *,
    enriched_manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    executable = [row for row in enriched_manifest.get("executable_request_intents", []) if isinstance(row, Mapping)]
    missing = [row for row in enriched_manifest.get("missing_url_request_intents", []) if isinstance(row, Mapping)]
    blocked = [row for row in enriched_manifest.get("blocked_request_intents", []) if isinstance(row, Mapping)]
    return {
        "contract_version": OPERATOR_CARD_CONTRACT_VERSION,
        "card_id": "concrete-url-manifest-operator-card-007b",
        "generated_at": GENERATED_AT,
        "what_changed_after_practical_007": [
            "Placeholder request intents were separated from executable concrete URL intents.",
            "Executable request count was capped at five.",
            "Operator approval for the next fetch remains pending.",
        ],
        "why_practical_007_blocked_fetch": [
            "The prior manifest had placeholder source references instead of concrete HTTP(S) URLs.",
            "The prior manifest had ten request intents while scoped approval allowed five.",
        ],
        "original_request_count": enriched_manifest.get("original_request_count"),
        "executable_request_count": enriched_manifest.get("executable_request_count"),
        "missing_url_count": enriched_manifest.get("missing_url_count"),
        "blocked_request_count": enriched_manifest.get("blocked_request_count"),
        "concrete_safe_urls": [
            {
                "request_intent_id": row.get("request_intent_id"),
                "market_id": row.get("market_id"),
                "market_title": row.get("market_title"),
                "source_category": row.get("source_category"),
                "source_url": row.get("source_url"),
                "reason": row.get("url_selection_reason"),
            }
            for row in executable
        ],
        "markets_still_needing_urls": [
            {
                "request_intent_id": row.get("request_intent_id"),
                "market_id": row.get("market_id"),
                "market_title": row.get("market_title"),
                "source_category": row.get("source_category"),
                "reason": row.get("missing_url_reason"),
            }
            for row in missing
        ],
        "blocked_requests": [
            {
                "request_intent_id": row.get("request_intent_id"),
                "market_id": row.get("market_id"),
                "source_category": row.get("source_category"),
                "reason": row.get("blocked_reason"),
            }
            for row in blocked
        ],
        "next_fetch_can_run_after_approval": preflight.get("would_be_ready_after_operator_approval") is True,
        "operator_must_approve_next": "Approve the pending scoped approval artifact for the future PRACTICAL-008 controlled public read-only fetch task.",
        "live_fetch_performed": False,
        "safety_summary": safe_summary(),
    }


def render_concrete_url_manifest_operator_card_markdown(card: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Concrete URL Manifest Operator Card",
        "",
        f"- Original request intents: {card.get('original_request_count')}",
        f"- Executable concrete URL requests: {card.get('executable_request_count')}",
        f"- Missing URL requests: {card.get('missing_url_count')}",
        f"- Blocked requests: {card.get('blocked_request_count')}",
        f"- Next fetch can run after approval: `{str(card.get('next_fetch_can_run_after_approval')).lower()}`",
        f"- Live fetch performed: `{str(card.get('live_fetch_performed')).lower()}`",
        "",
        "## What Changed After PRACTICAL-007",
        "",
        *bullet_lines(card.get("what_changed_after_practical_007", [])),
        "",
        "## Why PRACTICAL-007 Blocked Fetch",
        "",
        *bullet_lines(card.get("why_practical_007_blocked_fetch", [])),
        "",
        "## Concrete Safe URLs",
        "",
    ]
    for row in card.get("concrete_safe_urls", []):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}` market `{row.get('market_id')}`",
                f"  URL: `{row.get('source_url')}`",
                f"  Reason: {row.get('reason')}",
            ]
        )
    lines.extend(["", "## Markets Still Needing URLs", ""])
    for row in card.get("markets_still_needing_urls", []):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}` market `{row.get('market_id')}`",
                f"  Source category: `{row.get('source_category')}`",
                f"  Reason: {row.get('reason')}",
            ]
        )
    lines.extend(["", "## Blocked Requests", ""])
    for row in card.get("blocked_requests", []):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}` market `{row.get('market_id')}`",
                f"  Reason: {row.get('reason')}",
            ]
        )
    lines.extend(
        [
            "",
            "## Operator Must Approve Next",
            "",
            f"- {card.get('operator_must_approve_next')}",
        ]
    )
    return "\n".join(lines) + "\n"


def build_url_enrichment_safety_scan_report(*, artifact_dir: str | Path) -> dict[str, Any]:
    report = run_practical_safety_scan(artifact_dirs=[artifact_dir])
    report.update(
        {
            "live_fetch_performed": False,
            "openrouter_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "authenticated_endpoints_used": False,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "runtime_or_dispatcher_changes": False,
            "market_recommendation_generated": False,
            "probability_ev_edge_or_side_selection_generated": False,
            "operator_approval_granted": False,
            "url_enrichment_safety_scan_passed": report.get("safety_ok") is True,
        }
    )
    return report


def write_url_enrichment_package(
    *,
    original_manifest: Mapping[str, Any],
    source_dependency_map: Mapping[str, Any],
    normalized_market_inputs: Sequence[Mapping[str, Any]],
    manual_url_mapping_fixture: Mapping[str, Any],
    out_dir: str | Path,
    max_request_count: int = 5,
    fixture_mode: bool = False,
) -> dict[str, Any]:
    from pm_bot.practical.public_fetch_execution_preflight import (
        build_enriched_manifest_execution_preflight,
        render_enriched_manifest_execution_preflight_markdown,
    )

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    enriched = build_enriched_fetch_request_manifest(
        original_manifest=original_manifest,
        source_dependency_map=source_dependency_map,
        normalized_market_inputs=normalized_market_inputs,
        manual_url_mapping_fixture=manual_url_mapping_fixture,
        max_request_count=max_request_count,
        fixture_mode=fixture_mode,
    )
    safety_report = build_enriched_manifest_url_safety_report(enriched_manifest=enriched, fixture_mode=fixture_mode)
    approval = build_scoped_approval_for_enriched_manifest(enriched)
    preflight = build_enriched_manifest_execution_preflight(enriched_manifest=enriched, pending_approval=approval)
    card = build_concrete_url_manifest_operator_card(enriched_manifest=enriched, preflight=preflight)

    write_json(out / "enriched_fetch_request_manifest.json", enriched)
    write_text(out / "enriched_fetch_request_manifest.md", render_enriched_fetch_request_manifest_markdown(enriched))
    write_json(out / "enriched_manifest_url_safety_report.json", safety_report)
    write_text(out / "enriched_manifest_url_safety_report.md", render_enriched_manifest_url_safety_report_markdown(safety_report))
    write_json(out / "scoped_approval_for_enriched_manifest.pending.json", approval)
    write_text(out / "scoped_approval_for_enriched_manifest.pending.md", render_scoped_approval_for_enriched_manifest_markdown(approval))
    write_json(out / "enriched_manifest_execution_preflight.result.json", preflight)
    write_text(out / "enriched_manifest_execution_preflight.md", render_enriched_manifest_execution_preflight_markdown(preflight))
    write_json(out / "concrete_url_manifest_operator_card.json", card)
    write_text(out / "concrete_url_manifest_operator_card.md", render_concrete_url_manifest_operator_card_markdown(card))

    scan = build_url_enrichment_safety_scan_report(artifact_dir=out)
    write_json(out / "url_enrichment_safety_scan.result.json", scan)
    write_text(out / "url_enrichment_safety_scan.md", render_practical_safety_scan_markdown(scan))

    return {
        "enriched_manifest": enriched,
        "url_safety_report": safety_report,
        "approval": approval,
        "preflight": preflight,
        "operator_card": card,
        "safety_scan": scan,
    }


def load_normalized_market_inputs(paths: Sequence[str | Path]) -> list[dict[str, Any]]:
    return [load_json_object(path, label="normalized market input") for path in paths]


def _fixture_rows(fixture: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = fixture.get("mappings", fixture.get("url_mappings", []))
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _matching_fixture_row(rows: Sequence[Mapping[str, Any]], intent: Mapping[str, Any]) -> Mapping[str, Any] | None:
    market_id = clean_text(intent.get("market_id"))
    category = clean_text(intent.get("source_category"))
    source_name = clean_text(intent.get("source_name_or_placeholder") or intent.get("source_name")).lower()
    for row in rows:
        if clean_text(row.get("market_id")) != market_id:
            continue
        if clean_text(row.get("source_category")) != category:
            continue
        row_source_name = clean_text(row.get("source_name")).lower()
        if row_source_name and source_name and row_source_name != source_name:
            continue
        return row
    return None


def _candidate_url(intent: Mapping[str, Any], fixture_row: Mapping[str, Any] | None) -> str:
    if fixture_row is not None:
        raw_candidate = fixture_row.get("concrete_public_url")
        candidate = clean_text(raw_candidate) if raw_candidate is not None else ""
        if candidate:
            return candidate
    for key in ("source_reference", "source_reference_or_placeholder", "source_url", "url", "source_url_or_reference"):
        value = clean_text(intent.get(key))
        if _is_http_url(value):
            return value
    return ""


def _executable_candidate_intent(
    *,
    intent: Mapping[str, Any],
    candidate_url: str,
    original_index: int,
    fixture_row: Mapping[str, Any] | None,
) -> dict[str, Any]:
    source_name = clean_text(
        (fixture_row or {}).get("source_name")
        or intent.get("source_name_or_placeholder")
        or intent.get("source_name")
    )
    return {
        "request_intent_id": clean_text(intent.get("request_intent_id")),
        "market_id": clean_text(intent.get("market_id")),
        "market_title": clean_text(intent.get("market_title")),
        "source_category": clean_text(intent.get("source_category")),
        "source_name": source_name,
        "source_reference": candidate_url,
        "source_url": candidate_url,
        "method": clean_text(intent.get("method") or intent.get("http_method") or "GET").upper(),
        "reason_needed": clean_text(intent.get("reason_needed")),
        "expected_evidence_type": clean_text(
            (fixture_row or {}).get("expected_evidence_type") or intent.get("expected_evidence_type")
        ),
        "linked_hypothesis_id": clean_text(
            (fixture_row or {}).get("linked_hypothesis_id") or intent.get("linked_hypothesis_id")
        ),
        "source_plan_id": clean_text(intent.get("source_plan_id")),
        "save_evidence_as": clean_text(intent.get("save_evidence_as")),
        "requires_auth": intent.get("requires_auth") is True,
        "credentials_required": intent.get("credentials_required") is True,
        "cookies_required": intent.get("cookies_required") is True,
        "trading_or_order_endpoint": intent.get("trading_or_order_endpoint") is True,
        "wallet_or_signing_required": intent.get("wallet_or_signing_required") is True,
        "live_fetch_performed": False,
        "url_status": "concrete_safe_public_url",
        "url_selection_reason": clean_text((fixture_row or {}).get("reason")) or "concrete public URL came from local manifest input",
        "original_manifest_index": original_index,
        "category_priority": CATEGORY_PRIORITY.get(clean_text(intent.get("source_category")), 100),
    }


def _missing_row(
    intent: Mapping[str, Any],
    *,
    reason: str,
    original_index: int,
    dependency_source_ids: Sequence[str],
    normalized_source_reference_count: int,
) -> dict[str, Any]:
    return {
        "request_intent_id": clean_text(intent.get("request_intent_id")),
        "market_id": clean_text(intent.get("market_id")),
        "market_title": clean_text(intent.get("market_title")),
        "source_category": clean_text(intent.get("source_category")),
        "source_name_or_placeholder": clean_text(intent.get("source_name_or_placeholder") or intent.get("source_name")),
        "source_reference_or_placeholder": clean_text(intent.get("source_reference_or_placeholder") or intent.get("source_reference")),
        "expected_evidence_type": clean_text(intent.get("expected_evidence_type")),
        "linked_hypothesis_id": clean_text(intent.get("linked_hypothesis_id")),
        "missing_url_reason": reason,
        "url_status": "missing",
        "dependency_source_ids": list(dependency_source_ids),
        "normalized_source_reference_count": normalized_source_reference_count,
        "original_manifest_index": original_index,
        "live_fetch_performed": False,
    }


def _blocked_row(
    intent: Mapping[str, Any],
    *,
    reason: str,
    original_index: int,
    safety_blockers: Sequence[str],
    blocked_url_present: bool,
) -> dict[str, Any]:
    return {
        "request_intent_id": clean_text(intent.get("request_intent_id")),
        "market_id": clean_text(intent.get("market_id")),
        "market_title": clean_text(intent.get("market_title")),
        "source_category": clean_text(intent.get("source_category")),
        "source_name_or_placeholder": clean_text(intent.get("source_name_or_placeholder") or intent.get("source_name")),
        "expected_evidence_type": clean_text(intent.get("expected_evidence_type")),
        "linked_hypothesis_id": clean_text(intent.get("linked_hypothesis_id")),
        "blocked_reason": reason,
        "safety_blockers": list(safety_blockers),
        "blocked_url_present": blocked_url_present,
        "url_status": "blocked",
        "original_manifest_index": original_index,
        "live_fetch_performed": False,
    }


def _cap_safe_candidates(
    candidates: Sequence[Mapping[str, Any]],
    *,
    max_request_count: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ordered = sorted(
        (dict(row) for row in candidates),
        key=lambda row: (
            int(row.get("category_priority") or 100),
            int(row.get("original_manifest_index") or 0),
            clean_text(row.get("market_id")),
            clean_text(row.get("request_intent_id")),
        ),
    )
    selected = ordered[:max_request_count]
    omitted = [
        {
            "request_intent_id": clean_text(row.get("request_intent_id")),
            "market_id": clean_text(row.get("market_id")),
            "market_title": clean_text(row.get("market_title")),
            "source_category": clean_text(row.get("source_category")),
            "omitted_reason": f"safe candidate omitted because max_request_count is {max_request_count}",
            "concrete_public_url_omitted": True,
            "live_fetch_performed": False,
        }
        for row in ordered[max_request_count:]
    ]
    return selected, omitted


def _market_context_by_id(normalized_market_inputs: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, int]]:
    rows: dict[str, dict[str, int]] = {}
    for item in normalized_market_inputs:
        market_id = clean_text(item.get("market_id"))
        if not market_id:
            continue
        refs = [
            packet.get("source_url_or_reference")
            for packet in item.get("source_packets", [])
            if isinstance(packet, Mapping) and clean_text(packet.get("source_url_or_reference"))
        ]
        rows[market_id] = {"source_reference_count": len(refs)}
    return rows


def _dependency_ids_by_market(source_dependency_map: Mapping[str, Any]) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for dependency in source_dependency_map.get("dependencies", []):
        if not isinstance(dependency, Mapping):
            continue
        source_id = clean_text(dependency.get("source_id"))
        for market_id in dependency.get("market_ids", []):
            market_key = clean_text(market_id)
            if market_key and source_id:
                rows.setdefault(market_key, []).append(source_id)
    return {market_id: sorted(set(source_ids)) for market_id, source_ids in rows.items()}


def _is_http_url(value: str) -> bool:
    parsed = urlparse(clean_text(value))
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local-only PMBOT public URL enrichment artifacts.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--source-dependency-map", required=True)
    parser.add_argument("--manual-url-mapping", required=True)
    parser.add_argument("--normalized-input", action="append", default=[])
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-request-count", type=int, default=5)
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args(argv)
    write_url_enrichment_package(
        original_manifest=load_json_object(args.manifest, label="request manifest"),
        source_dependency_map=load_json_object(args.source_dependency_map, label="source dependency map"),
        normalized_market_inputs=load_normalized_market_inputs(args.normalized_input),
        manual_url_mapping_fixture=load_json_object(args.manual_url_mapping, label="manual URL mapping fixture"),
        out_dir=args.out_dir,
        max_request_count=args.max_request_count,
        fixture_mode=args.fixture_mode,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
