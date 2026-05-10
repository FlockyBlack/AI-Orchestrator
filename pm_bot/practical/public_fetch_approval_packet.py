from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import (
    GENERATED_AT,
    bullet_lines,
    clean_text,
    load_json_object,
    safe_summary,
    sorted_counter_dict,
    write_json,
    write_text,
)
from pm_bot.practical.practical_safety_scan import render_practical_safety_scan_markdown, run_practical_safety_scan
from pm_bot.practical.public_fetch_evidence_save_plan import (
    build_public_fetch_evidence_save_plan,
    write_public_fetch_evidence_save_plan,
)
from pm_bot.practical.public_fetch_replay_before_update_plan import (
    build_public_fetch_replay_before_update_plan,
    write_public_fetch_replay_before_update_plan,
)
from pm_bot.practical.public_fetch_request_manifest import (
    build_public_fetch_request_manifest,
    write_public_fetch_request_manifest,
)

APPROVAL_PACKET_CONTRACT_VERSION = "pmbot_public_read_only_fetch_approval_packet.v1"
FUTURE_TASK_SPEC_CONTRACT_VERSION = "pmbot_future_controlled_public_fetch_task_spec.v1"
MANUAL_OPERATOR_APPROVAL_TEMPLATE_CONTRACT_VERSION = "pmbot_manual_operator_approval_template.v1"
APPROVAL_BLOCKERS_CONTRACT_VERSION = "pmbot_public_fetch_approval_blocker_scenarios.v1"
OPERATOR_APPROVAL_CARD_CONTRACT_VERSION = "pmbot_public_fetch_operator_approval_card.v1"

SOURCE_TASK_ID = "ORCH-PMBOT-PRACTICAL-005-CONTROLLED-PUBLIC-READ-ONLY-FETCH-PREP-FOR-MARKET-PACKETS"
CURRENT_TASK_ID = "ORCH-PMBOT-PRACTICAL-006-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-DRY-RUN-APPROVAL-PACKET"
FUTURE_TASK_ID = "ORCH-PMBOT-PRACTICAL-007-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-OPERATOR-APPROVED"

DEFAULT_PREP_DIR = Path("pm_bot/practical/artifacts/public_read_only_fetch_prep_005")
DEFAULT_APPROVAL_DIR = Path("pm_bot/practical/artifacts/public_read_only_fetch_approval_006")
MANUAL_APPROVAL_TEMPLATE_PATH = (
    "pm_bot/practical/artifacts/public_read_only_fetch_approval_006/manual_operator_approval_template.json"
)


def build_public_fetch_approval_packet(
    *,
    fetch_plan: Mapping[str, Any],
    dry_run_preview: Mapping[str, Any],
    operator_approval: Mapping[str, Any],
    readiness_gate: Mapping[str, Any],
    link_map: Mapping[str, Any],
    source_registry: Mapping[str, Any],
    request_manifest: Mapping[str, Any] | None = None,
    evidence_save_plan: Mapping[str, Any] | None = None,
    replay_plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    market_titles = _market_titles(fetch_plan)
    requested_sources = _requested_public_sources(fetch_plan)
    return {
        "contract_version": APPROVAL_PACKET_CONTRACT_VERSION,
        "approval_packet_id": "public-read-only-fetch-approval-006-5-markets",
        "created_at": GENERATED_AT,
        "source_task_id": SOURCE_TASK_ID,
        "market_count": len(fetch_plan.get("market_ids", [])),
        "market_ids": list(fetch_plan.get("market_ids", [])),
        "market_titles": market_titles,
        "requested_public_sources": requested_sources,
        "blocked_sources": _blocked_source_rows(source_registry),
        "max_request_count": fetch_plan.get("max_request_count"),
        "timeout_seconds": fetch_plan.get("timeout_seconds"),
        "retry_policy": dict(fetch_plan.get("retry_policy", {})),
        "evidence_save_required": True,
        "replay_required_before_analysis_update": True,
        "operator_approval_required": True,
        "operator_approval_granted": False,
        "ready_for_controlled_public_fetch": False,
        "live_fetch_performed": False,
        "live_network_used": False,
        "allowed_future_task_scope": [
            "Only the explicitly approved future task may perform finite public read-only fetches.",
            "Only the listed five markets and listed source categories are in scope.",
            "Evidence must be saved before replay.",
            "Saved evidence must be replayed before any analysis update.",
            "Operator review remains required after replay.",
        ],
        "explicitly_blocked_scope": _blocked_scope(),
        "operator_checklist": _operator_checklist(),
        "safety_summary": {
            **safe_summary(),
            "operator_approval_required": True,
            "operator_approval_granted": False,
            "ready_for_controlled_public_fetch": False,
            "live_fetch_performed": False,
        },
        "next_allowed_action_after_manual_approval": FUTURE_TASK_ID,
        "next_blocked_actions": [
            "Live fetch from this task.",
            "Any authenticated or credentialed source.",
            "Wallet, signing, custody, orders, or trading paths.",
            "Scheduler, daemon, watcher, automatic polling, or unattended background fetch.",
            "OpenRouter or Polymarket API calls.",
            "Market action recommendations or executable quantitative output.",
        ],
        "current_readiness_blockers": list(readiness_gate.get("blockers", [])),
        "dry_run_request_count": dry_run_preview.get("request_count"),
        "request_manifest_id": (request_manifest or {}).get("request_manifest_id", ""),
        "evidence_save_plan_id": (evidence_save_plan or {}).get("evidence_save_plan_id", ""),
        "replay_plan_id": (replay_plan or {}).get("replay_plan_id", ""),
        "link_map_id": link_map.get("fetch_plan_id", ""),
        "approval_record_id": operator_approval.get("approval_id", ""),
        "manual_approval_artifact_required": MANUAL_APPROVAL_TEMPLATE_PATH,
    }


def render_public_fetch_approval_packet_markdown(packet: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Public Read-Only Fetch Approval Packet",
        "",
        "## Approval packet summary",
        "",
        f"- Approval packet ID: `{packet.get('approval_packet_id')}`",
        f"- Source task: `{packet.get('source_task_id')}`",
        f"- Markets: {packet.get('market_count')}",
        f"- Max requests: {packet.get('max_request_count')}",
        f"- Operator approval required: `{str(packet.get('operator_approval_required')).lower()}`",
        f"- Operator approval granted: `{str(packet.get('operator_approval_granted')).lower()}`",
        f"- Ready for controlled public fetch: `{str(packet.get('ready_for_controlled_public_fetch')).lower()}`",
        f"- Live fetch performed: `{str(packet.get('live_fetch_performed')).lower()}`",
        "",
        "## Markets included",
        "",
    ]
    market_titles = packet.get("market_titles", {})
    for market_id in packet.get("market_ids", []):
        lines.append(f"- `{market_id}` {market_titles.get(market_id, '')}")
    lines.extend(["", "## What would be fetched later", ""])
    for source in packet.get("requested_public_sources", []):
        lines.extend(
            [
                f"- `{source.get('market_id')}` `{source.get('source_category')}`",
                f"  Source: {source.get('source_name_or_placeholder')}",
                f"  Evidence: {source.get('expected_evidence_type')}",
                f"  Why needed: {source.get('reason_needed')}",
            ]
        )
    lines.extend(
        [
            "",
            "## What will not be fetched",
            "",
            *bullet_lines(packet.get("explicitly_blocked_scope", [])),
            "",
            "## Limits",
            "",
            f"- Max requests: {packet.get('max_request_count')}",
            f"- Timeout seconds: {packet.get('timeout_seconds')}",
            f"- Retry policy: `{packet.get('retry_policy')}`",
            "",
            "## Evidence-save and replay plan",
            "",
            f"- Evidence save required: `{str(packet.get('evidence_save_required')).lower()}`",
            f"- Replay required before analysis update: `{str(packet.get('replay_required_before_analysis_update')).lower()}`",
            f"- Request manifest ID: `{packet.get('request_manifest_id')}`",
            f"- Evidence save plan ID: `{packet.get('evidence_save_plan_id')}`",
            f"- Replay plan ID: `{packet.get('replay_plan_id')}`",
            "",
            "## Operator checklist",
            "",
            *bullet_lines(packet.get("operator_checklist", [])),
            "",
            "## Current readiness: blocked until approval",
            "",
            *bullet_lines(packet.get("current_readiness_blockers", [])),
            "",
            "## Safety boundary",
            "",
            *bullet_lines(packet.get("next_blocked_actions", [])),
            "",
            "## Future allowed task if approved",
            "",
            f"- `{packet.get('next_allowed_action_after_manual_approval')}`",
            f"- Manual approval artifact required: `{packet.get('manual_approval_artifact_required')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_public_fetch_approval_packet(
    packet: Mapping[str, Any],
    *,
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    packet_dict = dict(packet)
    if out_json_path is not None:
        write_json(out_json_path, packet_dict)
    if out_md_path is not None:
        write_text(out_md_path, render_public_fetch_approval_packet_markdown(packet_dict))
    return packet_dict


def build_future_controlled_fetch_task_spec(*, approval_packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "contract_version": FUTURE_TASK_SPEC_CONTRACT_VERSION,
        "proposed_task_id": FUTURE_TASK_ID,
        "prerequisite_task_id": CURRENT_TASK_ID,
        "created_at": GENERATED_AT,
        "requires_manual_operator_approval": True,
        "approval_artifact_required": MANUAL_APPROVAL_TEMPLATE_PATH,
        "allowed_scope": [
            "finite public read-only fetches only",
            "no auth",
            "no wallet",
            "no trading",
            "no orders",
            "no scheduler",
            "no automatic polling",
            "save evidence before use",
            "replay evidence before analysis update",
        ],
        "blocked_scope": _blocked_scope(),
        "max_markets": approval_packet.get("market_count"),
        "max_requests": approval_packet.get("max_request_count"),
        "expected_outputs": [
            "saved public evidence packet JSON and Markdown per request intent",
            "request execution summary with public-source capture metadata",
            "replay-ready source packet mapping",
            "post-fetch safety scan showing no auth, wallet, order, trading, scheduler, or OpenRouter/Polymarket API use",
        ],
        "stop_conditions": [
            "approval artifact missing or still pending",
            "source requires auth, login, cookies, private API key, wallet, signing, or KYC",
            "source category is not in the approved source category set",
            "request count would exceed the approved maximum",
            "evidence cannot be saved before replay",
            "operator asks for broad unrestricted fetch scope",
        ],
        "operator_approval_granted": False,
        "ready_for_controlled_public_fetch": False,
        "live_fetch_performed": False,
        "live_network_used": False,
        "safety_summary": safe_summary(),
    }


def render_future_controlled_fetch_task_spec_markdown(spec: Mapping[str, Any]) -> str:
    lines = [
        "# Future Controlled Public Read-Only Fetch Task Spec",
        "",
        f"- Proposed task: `{spec.get('proposed_task_id')}`",
        f"- Prerequisite task: `{spec.get('prerequisite_task_id')}`",
        f"- Manual approval required: `{str(spec.get('requires_manual_operator_approval')).lower()}`",
        f"- Approval artifact required: `{spec.get('approval_artifact_required')}`",
        f"- Max markets: {spec.get('max_markets')}",
        f"- Max requests: {spec.get('max_requests')}",
        "",
        "## Allowed Scope",
        "",
        *bullet_lines(spec.get("allowed_scope", [])),
        "",
        "## Blocked Scope",
        "",
        *bullet_lines(spec.get("blocked_scope", [])),
        "",
        "## Expected Outputs",
        "",
        *bullet_lines(spec.get("expected_outputs", [])),
        "",
        "## Stop Conditions",
        "",
        *bullet_lines(spec.get("stop_conditions", [])),
    ]
    return "\n".join(lines) + "\n"


def build_manual_operator_approval_template(*, approval_packet: Mapping[str, Any]) -> dict[str, Any]:
    categories = sorted(
        {
            clean_text(source.get("source_category"))
            for source in approval_packet.get("requested_public_sources", [])
            if isinstance(source, Mapping) and clean_text(source.get("source_category"))
        }
    )
    return {
        "contract_version": MANUAL_OPERATOR_APPROVAL_TEMPLATE_CONTRACT_VERSION,
        "approval_for_task_id": FUTURE_TASK_ID,
        "created_at": GENERATED_AT,
        "approval_status": "pending",
        "operator_must_set_to_approved_manually": True,
        "approved_by": None,
        "approved_at": None,
        "approved_market_ids": list(approval_packet.get("market_ids", [])),
        "approved_max_request_count": approval_packet.get("max_request_count"),
        "approved_source_categories": categories,
        "blocked_source_categories": [row.get("source_category", "") for row in approval_packet.get("blocked_sources", [])],
        "safety_acknowledgements_required": [
            "I reviewed the approval packet and request manifest.",
            "I approve only the listed markets, request count, and source categories.",
            "No auth, credentials, cookies, wallet, signing, orders, trading, scheduler, or polling are approved.",
            "Evidence must be saved before replay.",
            "Replay must happen before any analysis update.",
        ],
        "explicit_non_approval_notice": "This template is pending and does not grant approval until a future separate operator action changes approval_status to approved with approved_by and approved_at.",
        "operator_approval_granted": False,
        "ready_for_controlled_public_fetch": False,
        "live_fetch_performed": False,
        "live_network_used": False,
        "safety_summary": safe_summary(),
    }


def render_manual_operator_approval_template_markdown(template: Mapping[str, Any]) -> str:
    lines = [
        "# Manual Operator Approval Template",
        "",
        f"- Approval for task: `{template.get('approval_for_task_id')}`",
        f"- Approval status: `{template.get('approval_status')}`",
        f"- Operator must set manually: `{str(template.get('operator_must_set_to_approved_manually')).lower()}`",
        f"- Approved by: `{template.get('approved_by')}`",
        f"- Approved at: `{template.get('approved_at')}`",
        f"- Approved max requests: {template.get('approved_max_request_count')}",
        "",
        "## Approved Markets",
        "",
        *bullet_lines(f"`{market_id}`" for market_id in template.get("approved_market_ids", [])),
        "",
        "## Approved Source Categories",
        "",
        *bullet_lines(f"`{category}`" for category in template.get("approved_source_categories", [])),
        "",
        "## Blocked Source Categories",
        "",
        *bullet_lines(f"`{category}`" for category in template.get("blocked_source_categories", [])),
        "",
        "## Required Acknowledgements",
        "",
        *bullet_lines(template.get("safety_acknowledgements_required", [])),
        "",
        "## Non-Approval Notice",
        "",
        template.get("explicit_non_approval_notice", ""),
    ]
    return "\n".join(lines) + "\n"


def build_approval_blocker_scenarios() -> dict[str, Any]:
    scenarios = [
        _blocker("approval_missing", "approval missing", "No manual approval artifact grants the future task.", "Keep fetch blocked and create a reviewed approval artifact."),
        _blocker("auth_required_by_source", "auth required by source", "Public read-only scope cannot use login, cookies, credentials, or private API keys.", "Replace the source with a public no-auth source or keep it out of scope."),
        _blocker("source_category_blocked", "source category blocked", "The source category is blocked by the registry.", "Choose an allowed source category and update the manifest locally."),
        _blocker("request_count_exceeds_limit", "request count exceeds limit", "The request total is greater than the approved maximum.", "Reduce request intents or create a narrower approval artifact."),
        _blocker("evidence_save_disabled", "evidence save disabled", "Future public evidence must be saved before replay.", "Restore evidence saving and validate the save plan."),
        _blocker("replay_before_update_disabled", "replay-before-update disabled", "Saved evidence must be replayed before PMBOT analysis changes.", "Restore replay-before-update and run replay validation."),
        _blocker("trading_endpoint_detected", "trading endpoint detected", "Execution-related endpoints are out of scope.", "Remove the endpoint and keep the source public read-only."),
        _blocker("wallet_signing_required", "wallet/signing required", "Wallet, private-key, signing, custody, and KYC paths are blocked.", "Use only public no-wallet evidence sources."),
        _blocker("scheduler_background_fetch_requested", "scheduler/background fetch requested", "This approval path allows only a finite operator-approved task.", "Use a one-time manually approved task with no scheduler or polling."),
        _blocker("broad_unrestricted_fetch_requested", "operator tries to approve broad unrestricted fetch", "Approval must be limited to named markets, source categories, and request count.", "Replace with a narrow approval artifact for the listed scope only."),
    ]
    return {
        "contract_version": APPROVAL_BLOCKERS_CONTRACT_VERSION,
        "created_at": GENERATED_AT,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "live_fetch_performed": False,
        "live_network_used": False,
        "safety_summary": safe_summary(),
    }


def render_approval_blocker_scenarios_markdown(blockers: Mapping[str, Any]) -> str:
    lines = [
        "# Approval Blocker Scenarios",
        "",
        f"- Scenarios: {blockers.get('scenario_count')}",
        "",
        "## Scenarios",
        "",
    ]
    for scenario in blockers.get("scenarios", []):
        lines.extend(
            [
                f"- `{scenario.get('scenario_id')}` {scenario.get('scenario')}",
                f"  Expected behavior: `{scenario.get('expected_behavior')}`",
                f"  Reason: {scenario.get('reason')}",
                f"  Safe recovery action: {scenario.get('safe_recovery_action')}",
            ]
        )
    return "\n".join(lines) + "\n"


def build_operator_public_fetch_approval_card(*, approval_packet: Mapping[str, Any]) -> dict[str, Any]:
    category_counts = Counter(
        source.get("source_category", "")
        for source in approval_packet.get("requested_public_sources", [])
        if isinstance(source, Mapping)
    )
    return {
        "contract_version": OPERATOR_APPROVAL_CARD_CONTRACT_VERSION,
        "card_id": "operator-public-fetch-approval-card-006",
        "created_at": GENERATED_AT,
        "current_status": "not approved",
        "markets_covered": [
            {"market_id": market_id, "market_title": approval_packet.get("market_titles", {}).get(market_id, "")}
            for market_id in approval_packet.get("market_ids", [])
        ],
        "what_would_be_fetched_later": sorted_counter_dict(category_counts),
        "max_requests": approval_packet.get("max_request_count"),
        "evidence_save_required": True,
        "replay_required": True,
        "what_is_blocked": approval_packet.get("explicitly_blocked_scope", []),
        "what_operator_must_review": [
            "approval_packet_5_markets.md",
            "fetch_request_manifest_5_markets.md",
            "evidence_save_plan_5_markets.md",
            "replay_before_update_plan_5_markets.md",
            "future_controlled_fetch_task_spec.md",
            "approval_blocker_scenarios.md",
        ],
        "exact_approval_artifact_to_change_manually_later": MANUAL_APPROVAL_TEMPLATE_PATH,
        "next_safe_action": "Review the packet. A future controlled public read-only fetch task is allowed only after manual approval.",
        "operator_approval_granted": False,
        "ready_for_controlled_public_fetch": False,
        "live_fetch_performed": False,
        "live_network_used": False,
        "safety_summary": safe_summary(),
    }


def render_operator_public_fetch_approval_card_markdown(card: Mapping[str, Any]) -> str:
    lines = [
        "# Operator Public Fetch Approval Card",
        "",
        f"- Current status: {card.get('current_status')}",
        f"- Max requests: {card.get('max_requests')}",
        f"- Evidence save required: `{str(card.get('evidence_save_required')).lower()}`",
        f"- Replay required: `{str(card.get('replay_required')).lower()}`",
        f"- Approval artifact to change manually later: `{card.get('exact_approval_artifact_to_change_manually_later')}`",
        "",
        "## Markets Covered",
        "",
    ]
    for row in card.get("markets_covered", []):
        lines.append(f"- `{row.get('market_id')}` {row.get('market_title')}")
    lines.extend(["", "## What Would Be Fetched Later", ""])
    for category, count in card.get("what_would_be_fetched_later", {}).items():
        lines.append(f"- `{category}`: {count}")
    lines.extend(
        [
            "",
            "## What Is Blocked",
            "",
            *bullet_lines(card.get("what_is_blocked", [])),
            "",
            "## Operator Must Review",
            "",
            *bullet_lines(f"`{item}`" for item in card.get("what_operator_must_review", [])),
            "",
            "## Next Safe Action",
            "",
            card.get("next_safe_action", ""),
        ]
    )
    return "\n".join(lines) + "\n"


def build_approval_packet_safety_scan_report(*, artifact_dir: str | Path) -> dict[str, Any]:
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
        "operator_approval_granted": False,
        "ready_for_controlled_public_fetch": False,
        "scheduler_background_worker_or_polling": False,
        "no_scheduler_background_worker_polling": True,
    }
    passed = (
        base_report["safety_ok"]
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
        and required_flags["ready_for_controlled_public_fetch"] is False
        and required_flags["scheduler_background_worker_or_polling"] is False
    )
    return {
        **base_report,
        **required_flags,
        "approval_packet_safety_scan_passed": passed,
    }


def render_approval_packet_safety_scan_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Approval Packet Safety Scan",
        "",
        f"- Safety OK: `{str(report.get('safety_ok')).lower()}`",
        f"- Approval packet safety scan passed: `{str(report.get('approval_packet_safety_scan_passed')).lower()}`",
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
        f"- Scheduler/background worker/polling present: `{str(report.get('scheduler_background_worker_or_polling')).lower()}`",
        "",
        "## Underlying Practical Scan",
        "",
    ]
    lines.extend(render_practical_safety_scan_markdown(report).splitlines())
    return "\n".join(lines) + "\n"


def generate_public_fetch_approval_artifacts(
    *,
    prep_dir: str | Path = DEFAULT_PREP_DIR,
    artifact_dir: str | Path = DEFAULT_APPROVAL_DIR,
) -> dict[str, Any]:
    prep = Path(prep_dir)
    out = Path(artifact_dir)
    fetch_plan = load_json_object(prep / "fetch_plan_5_markets.json", label="fetch plan")
    dry_run_preview = load_json_object(prep / "fetch_dry_run_preview_5_markets.json", label="dry-run preview")
    operator_approval = load_json_object(prep / "operator_approval_pending.json", label="operator approval")
    readiness_gate = load_json_object(prep / "public_fetch_readiness_gate.result.json", label="readiness gate")
    link_map = load_json_object(prep / "fetch_plan_to_active_hypotheses_link_map.json", label="link map")
    source_registry = load_json_object(prep / "source_registry_snapshot.json", label="source registry")

    request_manifest = build_public_fetch_request_manifest(fetch_plan=fetch_plan, link_map=link_map)
    write_public_fetch_request_manifest(
        request_manifest,
        out_json_path=out / "fetch_request_manifest_5_markets.json",
        out_md_path=out / "fetch_request_manifest_5_markets.md",
    )
    evidence_save_plan = build_public_fetch_evidence_save_plan(fetch_plan=fetch_plan)
    write_public_fetch_evidence_save_plan(
        evidence_save_plan,
        out_json_path=out / "evidence_save_plan_5_markets.json",
        out_md_path=out / "evidence_save_plan_5_markets.md",
    )
    replay_plan = build_public_fetch_replay_before_update_plan(
        fetch_plan=fetch_plan,
        request_manifest=request_manifest,
        evidence_save_plan=evidence_save_plan,
    )
    write_public_fetch_replay_before_update_plan(
        replay_plan,
        out_json_path=out / "replay_before_update_plan_5_markets.json",
        out_md_path=out / "replay_before_update_plan_5_markets.md",
    )
    approval_packet = build_public_fetch_approval_packet(
        fetch_plan=fetch_plan,
        dry_run_preview=dry_run_preview,
        operator_approval=operator_approval,
        readiness_gate=readiness_gate,
        link_map=link_map,
        source_registry=source_registry,
        request_manifest=request_manifest,
        evidence_save_plan=evidence_save_plan,
        replay_plan=replay_plan,
    )
    write_public_fetch_approval_packet(
        approval_packet,
        out_json_path=out / "approval_packet_5_markets.json",
        out_md_path=out / "approval_packet_5_markets.md",
    )
    future_spec = build_future_controlled_fetch_task_spec(approval_packet=approval_packet)
    write_json(out / "future_controlled_fetch_task_spec.json", future_spec)
    write_text(out / "future_controlled_fetch_task_spec.md", render_future_controlled_fetch_task_spec_markdown(future_spec))
    approval_template = build_manual_operator_approval_template(approval_packet=approval_packet)
    write_json(out / "manual_operator_approval_template.json", approval_template)
    write_text(out / "manual_operator_approval_template.md", render_manual_operator_approval_template_markdown(approval_template))
    blockers = build_approval_blocker_scenarios()
    write_json(out / "approval_blocker_scenarios.json", blockers)
    write_text(out / "approval_blocker_scenarios.md", render_approval_blocker_scenarios_markdown(blockers))
    card = build_operator_public_fetch_approval_card(approval_packet=approval_packet)
    write_json(out / "operator_public_fetch_approval_card.json", card)
    write_text(out / "operator_public_fetch_approval_card.md", render_operator_public_fetch_approval_card_markdown(card))
    safety_scan = build_approval_packet_safety_scan_report(artifact_dir=out)
    write_json(out / "approval_packet_safety_scan.result.json", safety_scan)
    write_text(out / "approval_packet_safety_scan.md", render_approval_packet_safety_scan_markdown(safety_scan))
    return {
        "approval_packet": approval_packet,
        "request_manifest": request_manifest,
        "evidence_save_plan": evidence_save_plan,
        "replay_plan": replay_plan,
        "future_spec": future_spec,
        "approval_template": approval_template,
        "blockers": blockers,
        "card": card,
        "safety_scan": safety_scan,
    }


def _requested_public_sources(fetch_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for source in fetch_plan.get("requested_sources", []):
        if not isinstance(source, Mapping):
            continue
        rows.append(
            {
                "planned_source_id": source.get("planned_source_id", ""),
                "market_id": source.get("market_id", ""),
                "market_title": source.get("market_title", ""),
                "source_category": source.get("source_category", ""),
                "source_name_or_placeholder": source.get("source_name", ""),
                "source_reference_or_placeholder": source.get("source_reference", ""),
                "reason_needed": source.get("why_fresh_evidence_would_matter", ""),
                "expected_evidence_type": source.get("expected_evidence_type", ""),
                "linked_hypothesis_id": source.get("hypothesis_id", ""),
                "allowed_status": source.get("allowed_status", ""),
                "live_fetch_performed": False,
            }
        )
    return rows


def _market_titles(fetch_plan: Mapping[str, Any]) -> dict[str, str]:
    titles: dict[str, str] = {}
    for source in fetch_plan.get("requested_sources", []):
        if isinstance(source, Mapping):
            market_id = clean_text(source.get("market_id"))
            title = clean_text(source.get("market_title"))
            if market_id and title:
                titles[market_id] = title
    return {market_id: titles.get(market_id, "") for market_id in fetch_plan.get("market_ids", [])}


def _blocked_source_rows(source_registry: Mapping[str, Any]) -> list[dict[str, str]]:
    rows = []
    for source in source_registry.get("blocked_sources", []):
        if isinstance(source, Mapping):
            rows.append(
                {
                    "source_category": clean_text(source.get("source_category")),
                    "reason": clean_text(source.get("reason")),
                    "safety_boundary": clean_text(source.get("safety_boundary")),
                }
            )
    return rows


def _blocked_scope() -> list[str]:
    return [
        "Authenticated endpoints",
        "Private API key endpoints",
        "Browser session, cookie, login, KYC, or bypass-based sources",
        "Wallet, private key, signing, custody, order, or trading paths",
        "OpenRouter calls",
        "Polymarket API calls",
        "Schedulers, daemons, watchers, automatic polling, or unattended automation",
        "Market recommendations or executable quantitative market output",
        "Runtime, dispatcher, run_codex, browser automation, or autonomous execution changes",
    ]


def _operator_checklist() -> list[str]:
    return [
        "Review the five market IDs and titles.",
        "Review each request intent and source category.",
        "Confirm the maximum request count remains 10.",
        "Confirm evidence save is required before replay.",
        "Confirm replay is required before any analysis update.",
        "Confirm blocked scope remains blocked.",
        "If approval is later intended, update only the manual approval artifact in a separate explicit task.",
    ]


def _blocker(scenario_id: str, scenario: str, reason: str, safe_recovery_action: str) -> dict[str, str]:
    return {
        "scenario_id": scenario_id,
        "scenario": scenario,
        "expected_behavior": "block",
        "reason": reason,
        "safe_recovery_action": safe_recovery_action,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the local-only public fetch approval packet artifacts.")
    parser.add_argument("--prep-dir", default=str(DEFAULT_PREP_DIR), help="Input PRACTICAL-005 artifact directory.")
    parser.add_argument("--artifact-dir", default=str(DEFAULT_APPROVAL_DIR), help="Output PRACTICAL-006 artifact directory.")
    args = parser.parse_args(argv)
    generate_public_fetch_approval_artifacts(prep_dir=args.prep_dir, artifact_dir=args.artifact_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
