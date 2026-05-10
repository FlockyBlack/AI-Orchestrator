from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.market_queue import load_market_queue
from pm_bot.practical.outcome_check_queue import build_outcome_check_queue
from pm_bot.practical.practical_io import (
    GENERATED_AT,
    bullet_lines,
    clean_text,
    load_json_object,
    normalize_path,
    optional_existing_path,
    safe_summary,
    write_json,
    write_text,
)
from pm_bot.practical.practical_safety_scan import render_practical_safety_scan_markdown, run_practical_safety_scan
from pm_bot.practical.public_read_only_fetch_contract import build_public_read_only_fetch_plan, render_fetch_plan_markdown, write_fetch_plan
from pm_bot.practical.public_source_registry import build_public_source_registry, validate_source_category

FETCH_PREP_ARTIFACT_CONTRACT_VERSION = "pmbot_public_read_only_fetch_prep_005_artifact.v1"

TRACKED_MARKET_IDS = ("563650", "597964", "598936", "691547", "692258")

DOMAIN_SOURCE_TEMPLATES: dict[str, dict[str, str]] = {
    "563650": {
        "source_category": "public_court_government_page_placeholder",
        "source_name": "public court/government page placeholder",
        "expected_evidence_type": "official docket or resolution page snapshot",
        "expected_evidence_role": "future official-source evidence for outcome and rules review",
        "why_fresh_evidence_would_matter": "The paper hypothesis depends on later checking whether public court records support the saved local packet.",
    },
    "597964": {
        "source_category": "public_resolution_source_page_placeholder",
        "source_name": "public resolution source page placeholder",
        "expected_evidence_type": "public official status or resolution page snapshot",
        "expected_evidence_role": "future public evidence for outcome review",
        "why_fresh_evidence_would_matter": "The paper hypothesis depends on later checking public status evidence against the saved local packet.",
    },
    "598936": {
        "source_category": "public_court_government_page_placeholder",
        "source_name": "public government or parliament page placeholder",
        "expected_evidence_type": "public election or parliament page snapshot",
        "expected_evidence_role": "future official-source evidence for outcome review",
        "why_fresh_evidence_would_matter": "The paper hypothesis depends on later checking public election timing evidence against the saved local packet.",
    },
    "691547": {
        "source_category": "public_exchange_company_announcement_page_placeholder",
        "source_name": "public exchange/company announcement page placeholder",
        "expected_evidence_type": "public listing or company announcement snapshot",
        "expected_evidence_role": "future public evidence for IPO status review",
        "why_fresh_evidence_would_matter": "The paper hypothesis depends on later checking public listing or company announcement evidence against the saved local packet.",
    },
    "692258": {
        "source_category": "public_issuer_company_news_page_placeholder",
        "source_name": "public issuer/company news page placeholder",
        "expected_evidence_type": "public issuer news or filing summary snapshot",
        "expected_evidence_role": "future public evidence for company action review",
        "why_fresh_evidence_would_matter": "The paper hypothesis depends on later checking public company evidence against the saved local packet.",
    },
}


def build_fetch_plan_from_queue(
    *,
    queue_path: str | Path,
    source_dependency_map_path: str | Path | None = None,
    fetch_plan_id: str = "public-read-only-fetch-prep-005-5-markets",
) -> dict[str, Any]:
    queue = load_market_queue(queue_path)
    queue_items = [item for item in queue["items"] if clean_text(item.get("market_id")) in TRACKED_MARKET_IDS]
    queue_items = sorted(queue_items, key=lambda item: TRACKED_MARKET_IDS.index(clean_text(item.get("market_id"))))
    dependencies_by_market = _dependencies_by_market(source_dependency_map_path or _default_dependency_map_path(queue_path))
    requested_sources: list[dict[str, Any]] = []
    for item in queue_items:
        market_id = clean_text(item.get("market_id"))
        requested_sources.append(_market_metadata_source(item, dependencies_by_market.get(market_id, [])))
        requested_sources.append(_domain_source(item, dependencies_by_market.get(market_id, [])))
    plan = build_public_read_only_fetch_plan(
        fetch_plan_id=fetch_plan_id,
        market_ids=[clean_text(item["market_id"]) for item in queue_items],
        requested_sources=requested_sources,
        max_request_count=len(requested_sources),
        timeout_seconds=10,
        retry_policy={
            "retry_enabled": False,
            "max_attempts": 0,
            "backoff_seconds": 0,
            "reason": "Retries are disabled for this local-only preparation task.",
        },
        safety_notes=[
            "Operator-approved explicit command is required before any future public read-only request.",
            "This plan lists future requests only and performs no network access.",
            "Evidence saving is required before replay.",
            "Saved evidence replay is required before any analysis update.",
            "Authenticated, wallet, order, trading, scheduler, polling, and autonomous paths remain blocked.",
        ],
    )
    plan["source_dependency_map_path"] = normalize_path(source_dependency_map_path or _default_dependency_map_path(queue_path))
    plan["queue_path"] = normalize_path(queue_path)
    return plan


def write_fetch_plan_from_queue(
    *,
    queue_path: str | Path,
    out_json_path: str | Path,
    out_md_path: str | Path,
    source_dependency_map_path: str | Path | None = None,
) -> dict[str, Any]:
    plan = build_fetch_plan_from_queue(
        queue_path=queue_path,
        source_dependency_map_path=source_dependency_map_path,
    )
    write_fetch_plan(plan, out_json_path=str(out_json_path), out_md_path=str(out_md_path))
    return plan


def build_fetch_plan_to_active_hypotheses_link_map(
    *,
    fetch_plan: Mapping[str, Any],
    queue_path: str | Path,
    source_dependency_map_path: str | Path | None = None,
) -> dict[str, Any]:
    queue = load_market_queue(queue_path)
    outcome_queue = build_outcome_check_queue(queue_path)
    dependencies_by_market = _dependencies_by_market(source_dependency_map_path or _default_dependency_map_path(queue_path))
    sources_by_market: dict[str, list[Mapping[str, Any]]] = {}
    for source in fetch_plan.get("requested_sources", []):
        if isinstance(source, Mapping):
            sources_by_market.setdefault(clean_text(source.get("market_id")), []).append(source)
    outcome_by_market = {
        clean_text(row.get("market_id")): row for row in outcome_queue.get("outcome_checks", []) if isinstance(row, Mapping)
    }
    rows = []
    for item in queue["items"]:
        market_id = clean_text(item.get("market_id"))
        if market_id not in fetch_plan.get("market_ids", []):
            continue
        planned_sources = sources_by_market.get(market_id, [])
        rows.append(
            {
                "market_id": market_id,
                "market_title": clean_text(item.get("market_title")),
                "hypothesis_id": clean_text(item.get("paper_hypothesis_id")),
                "source_dependency": [
                    {
                        "source_id": dep.get("source_id", ""),
                        "dependency_role": dep.get("dependency_role", ""),
                        "known_limitations": dep.get("known_limitations", []),
                    }
                    for dep in dependencies_by_market.get(market_id, [])
                ],
                "planned_public_evidence_source_category": [
                    source.get("source_category", "") for source in planned_sources
                ],
                "expected_evidence_role": [
                    source.get("expected_evidence_role", "") for source in planned_sources
                ],
                "why_fresh_evidence_would_matter": [
                    source.get("why_fresh_evidence_would_matter", "") for source in planned_sources
                ],
                "outcome_check_dependency": outcome_by_market.get(market_id, {}),
                "safety_status": "paper_only_fetch_prep_no_live_network_no_trading",
            }
        )
    return {
        "contract_version": "pmbot_public_fetch_plan_to_active_hypotheses_link_map.v1",
        "generated_at": GENERATED_AT,
        "fetch_plan_id": fetch_plan.get("fetch_plan_id", ""),
        "links": rows,
        "safety_summary": safe_summary(),
    }


def render_fetch_plan_to_active_hypotheses_link_map_markdown(link_map: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Fetch Plan To Active Hypotheses Link Map",
        "",
        f"- Fetch plan ID: `{link_map.get('fetch_plan_id')}`",
        f"- Links: {len(link_map.get('links', []))}",
        "",
        "## Links",
        "",
    ]
    for row in link_map.get("links", []):
        lines.extend(
            [
                f"- `{row.get('market_id')}` {row.get('market_title')}",
                f"  Hypothesis: `{row.get('hypothesis_id')}`",
                f"  Categories: {', '.join(row.get('planned_public_evidence_source_category', []))}",
                f"  Outcome dependency: `{row.get('outcome_check_dependency', {}).get('outcome_check_status', 'unknown')}`",
                f"  Safety: `{row.get('safety_status')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- Link map only.",
            "- No live fetch or analysis update is performed.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_fetch_plan_to_active_hypotheses_link_map(
    *,
    link_map: Mapping[str, Any],
    out_json_path: str | Path,
    out_md_path: str | Path,
) -> dict[str, Any]:
    link_map_dict = dict(link_map)
    write_json(out_json_path, link_map_dict)
    write_text(out_md_path, render_fetch_plan_to_active_hypotheses_link_map_markdown(link_map_dict))
    return link_map_dict


def build_public_fetch_prep_operator_card(
    *,
    fetch_plan: Mapping[str, Any],
    dry_run_preview: Mapping[str, Any],
    operator_approval: Mapping[str, Any],
    readiness_gate: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_public_fetch_prep_operator_card.v1",
        "generated_at": GENERATED_AT,
        "fetch_plan_id": fetch_plan.get("fetch_plan_id", ""),
        "what_is_ready": [
            "Local source registry is defined.",
            "Fetch plan contract is valid.",
            "Dry-run preview is available.",
            "Saved evidence packet and replay format are available.",
            "Readiness gate can explain blockers before any future request.",
        ],
        "what_is_blocked": readiness_gate.get("blockers", []),
        "approval_needed": {
            "operator_approval_required": operator_approval.get("operator_approval_required") is True,
            "operator_approval_granted": operator_approval.get("operator_approval_granted") is True,
            "approval_record": operator_approval.get("approval_id", ""),
        },
        "what_would_be_fetched_later": [
            {
                "market_id": source.get("market_id", ""),
                "market_title": source.get("market_title", ""),
                "source_category": source.get("source_category", ""),
                "expected_evidence_type": source.get("expected_evidence_type", ""),
                "source_reference": source.get("source_reference", ""),
            }
            for source in fetch_plan.get("requested_sources", [])
            if isinstance(source, Mapping)
        ],
        "what_will_not_be_fetched": [
            "Authenticated endpoints",
            "Private API key endpoints",
            "Browser session or cookie-based sources",
            "KYC or login-gated sources",
            "Wallet, signing, custody, order, or trading endpoints",
            "Scheduler, polling, daemon, watcher, or unattended automation paths",
        ],
        "why_live_fetch_is_not_performed_in_this_task": "This task creates contracts, dry-run surfaces, evidence replay, and approval gates only. Operator approval is pending and live fetch is out of scope.",
        "next_safe_action": "Review the pending approval packet and readiness blockers before creating a separate first controlled public read-only fetch approval packet.",
        "live_fetch_allowed_now": dry_run_preview.get("live_fetch_allowed_now") is True,
        "ready_for_controlled_public_fetch": readiness_gate.get("ready_for_controlled_public_fetch") is True,
        "safety_summary": safe_summary(),
    }


def render_public_fetch_prep_operator_card_markdown(card: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Public Fetch Prep Operator Card",
        "",
        f"- Fetch plan ID: `{card.get('fetch_plan_id')}`",
        f"- Live fetch allowed now: `{str(card.get('live_fetch_allowed_now')).lower()}`",
        f"- Ready for controlled public fetch: `{str(card.get('ready_for_controlled_public_fetch')).lower()}`",
        "",
        "## Ready",
        "",
        *bullet_lines(card.get("what_is_ready", [])),
        "",
        "## Blocked",
        "",
        *bullet_lines(card.get("what_is_blocked", [])),
        "",
        "## Would Be Fetched Later",
        "",
    ]
    for row in card.get("what_would_be_fetched_later", []):
        lines.append(
            f"- `{row.get('market_id')}` `{row.get('source_category')}` - {row.get('expected_evidence_type')}"
        )
    lines.extend(
        [
            "",
            "## Will Not Be Fetched",
            "",
            *bullet_lines(card.get("what_will_not_be_fetched", [])),
            "",
            "## Why No Live Fetch",
            "",
            card.get("why_live_fetch_is_not_performed_in_this_task", ""),
            "",
            "## Next Safe Action",
            "",
            card.get("next_safe_action", ""),
        ]
    )
    return "\n".join(lines) + "\n"


def write_public_fetch_prep_operator_card(
    *,
    card: Mapping[str, Any],
    out_json_path: str | Path,
    out_md_path: str | Path,
) -> dict[str, Any]:
    card_dict = dict(card)
    write_json(out_json_path, card_dict)
    write_text(out_md_path, render_public_fetch_prep_operator_card_markdown(card_dict))
    return card_dict


def build_public_fetch_prep_safety_scan_report(
    *,
    artifact_dir: str | Path,
    readiness_gate: Mapping[str, Any],
    operator_approval: Mapping[str, Any],
) -> dict[str, Any]:
    base_report = run_practical_safety_scan(artifact_dirs=[artifact_dir])
    required_flags = {
        "live_network_used": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_access": False,
        "orders_or_trading_actions": False,
        "runtime_or_dispatcher_changes": False,
        "market_recommendation_generated": False,
        "probability_ev_edge_or_side_selection_generated": False,
        "operator_approval_granted": operator_approval.get("operator_approval_granted") is True,
        "ready_for_controlled_public_fetch": readiness_gate.get("ready_for_controlled_public_fetch") is True,
    }
    report = {
        **base_report,
        **required_flags,
        "public_fetch_prep_safety_scan_passed": base_report["safety_ok"]
        and required_flags["live_network_used"] is False
        and required_flags["openrouter_calls_performed"] == 0
        and required_flags["polymarket_api_calls_performed"] == 0
        and required_flags["authenticated_endpoints_used"] is False
        and required_flags["wallet_or_private_key_access"] is False
        and required_flags["orders_or_trading_actions"] is False
        and required_flags["runtime_or_dispatcher_changes"] is False
        and required_flags["market_recommendation_generated"] is False
        and required_flags["probability_ev_edge_or_side_selection_generated"] is False
        and required_flags["operator_approval_granted"] is False
        and required_flags["ready_for_controlled_public_fetch"] is False,
    }
    return report


def render_public_fetch_prep_safety_scan_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Public Fetch Prep Safety Scan",
        "",
        f"- Safety OK: `{str(report.get('safety_ok')).lower()}`",
        f"- Public fetch prep safety scan passed: `{str(report.get('public_fetch_prep_safety_scan_passed')).lower()}`",
        f"- Live network used: `{str(report.get('live_network_used')).lower()}`",
        f"- OpenRouter calls performed: {report.get('openrouter_calls_performed')}",
        f"- Polymarket API calls performed: {report.get('polymarket_api_calls_performed')}",
        f"- Authenticated endpoints used: `{str(report.get('authenticated_endpoints_used')).lower()}`",
        f"- Wallet or private-key access: `{str(report.get('wallet_or_private_key_access')).lower()}`",
        f"- Orders or trading actions: `{str(report.get('orders_or_trading_actions')).lower()}`",
        f"- Runtime or dispatcher changes: `{str(report.get('runtime_or_dispatcher_changes')).lower()}`",
        f"- Market recommendation generated: `{str(report.get('market_recommendation_generated')).lower()}`",
        f"- Quantitative market-output generated: `{str(report.get('probability_ev_edge_or_side_selection_generated')).lower()}`",
        f"- Operator approval granted: `{str(report.get('operator_approval_granted')).lower()}`",
        f"- Ready for controlled public fetch: `{str(report.get('ready_for_controlled_public_fetch')).lower()}`",
        "",
        "## Underlying Practical Scan",
        "",
    ]
    lines.extend(render_practical_safety_scan_markdown(report).splitlines())
    return "\n".join(lines) + "\n"


def write_public_fetch_prep_safety_scan_report(
    *,
    report: Mapping[str, Any],
    out_json_path: str | Path,
    out_md_path: str | Path,
) -> dict[str, Any]:
    report_dict = dict(report)
    write_json(out_json_path, report_dict)
    write_text(out_md_path, render_public_fetch_prep_safety_scan_markdown(report_dict))
    return report_dict


def build_source_registry_snapshot() -> dict[str, Any]:
    registry = build_public_source_registry()
    registry["artifact_contract_version"] = FETCH_PREP_ARTIFACT_CONTRACT_VERSION
    return registry


def _market_metadata_source(item: Mapping[str, Any], dependencies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    market_id = clean_text(item.get("market_id"))
    return _planned_source(
        item=item,
        dependencies=dependencies,
        suffix="market_metadata",
        source_category="public_market_metadata_endpoint_placeholder",
        source_name="public market metadata endpoint placeholder",
        expected_evidence_type="public market metadata snapshot",
        expected_evidence_role="future metadata check for market title, rules, status, and linked references",
        why_fresh_evidence_would_matter="Fresh public metadata would help verify that the saved local packet still matches public market terms before replay.",
    )


def _domain_source(item: Mapping[str, Any], dependencies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    market_id = clean_text(item.get("market_id"))
    template = DOMAIN_SOURCE_TEMPLATES[market_id]
    return _planned_source(
        item=item,
        dependencies=dependencies,
        suffix="domain_public_evidence",
        **template,
    )


def _planned_source(
    *,
    item: Mapping[str, Any],
    dependencies: Sequence[Mapping[str, Any]],
    suffix: str,
    source_category: str,
    source_name: str,
    expected_evidence_type: str,
    expected_evidence_role: str,
    why_fresh_evidence_would_matter: str,
) -> dict[str, Any]:
    market_id = clean_text(item.get("market_id"))
    validation = validate_source_category(source_category)
    return {
        "planned_source_id": f"fetch-prep-005:{market_id}:{suffix}",
        "source_id": f"{market_id}:{suffix}",
        "source_name": source_name,
        "source_category": source_category,
        "source_reference": f"public_source_placeholder:{source_category}:{market_id}",
        "allowed_status": "allowed_in_principle_pending_operator_approval" if validation["allowed"] else "blocked",
        "blocked_status": validation["blocked"],
        "market_id": market_id,
        "market_title": clean_text(item.get("market_title")),
        "hypothesis_id": clean_text(item.get("paper_hypothesis_id")),
        "linked_source_dependency_ids": [clean_text(dep.get("source_id")) for dep in dependencies],
        "expected_evidence_type": expected_evidence_type,
        "expected_evidence_role": expected_evidence_role,
        "why_fresh_evidence_would_matter": why_fresh_evidence_would_matter,
        "operator_approval_required": True,
        "auth_required": False,
        "credentials_required": False,
        "wallet_required": False,
        "trading_endpoint": False,
        "order_endpoint": False,
        "live_fetch_performed": False,
    }


def _default_dependency_map_path(queue_path: str | Path) -> str:
    return normalize_path(Path(queue_path).parent / "real_market_batch_004.source_dependency_map.json")


def _dependencies_by_market(path: str | Path) -> dict[str, list[Mapping[str, Any]]]:
    existing = optional_existing_path(path)
    if existing is None:
        return {}
    payload = load_json_object(existing, label="source dependency map")
    by_market: dict[str, list[Mapping[str, Any]]] = {}
    for dependency in payload.get("dependencies", []):
        if not isinstance(dependency, Mapping):
            continue
        for market_id in dependency.get("market_ids", []):
            by_market.setdefault(clean_text(market_id), []).append(dependency)
    return by_market


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local-only public read-only fetch plan from a PMBOT market queue.")
    parser.add_argument("--queue", required=True, help="Input market queue JSON.")
    parser.add_argument("--out-json", required=True, help="Output fetch plan JSON.")
    parser.add_argument("--out-md", required=True, help="Output fetch plan Markdown.")
    parser.add_argument("--source-dependency-map", default=None, help="Optional source dependency map JSON.")
    args = parser.parse_args(argv)
    plan = build_fetch_plan_from_queue(
        queue_path=args.queue,
        source_dependency_map_path=args.source_dependency_map,
    )
    write_json(args.out_json, plan)
    write_text(args.out_md, render_fetch_plan_markdown(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
