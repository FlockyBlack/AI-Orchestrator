from __future__ import annotations

import argparse
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, load_json_object, safe_summary, write_json, write_text
from pm_bot.practical.public_fetch_dry_run_preview import build_fetch_dry_run_preview
from pm_bot.practical.public_read_only_fetch_contract import validate_fetch_plan
from pm_bot.practical.public_source_registry import build_public_source_registry, validate_requested_source

READINESS_GATE_CONTRACT_VERSION = "pmbot_public_read_only_fetch_readiness_gate.v1"


def evaluate_public_fetch_readiness(
    *,
    fetch_plan: Mapping[str, Any],
    approval: Mapping[str, Any],
    dry_run_preview: Mapping[str, Any] | None = None,
    source_registry: Mapping[str, Any] | None = None,
    safety_scan_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    preview = dict(dry_run_preview or build_fetch_dry_run_preview(fetch_plan))
    registry = dict(source_registry or build_public_source_registry())
    validation = validate_fetch_plan(fetch_plan)
    blockers: list[str] = []
    warnings: list[str] = []
    if not validation["valid"]:
        blockers.extend(validation["errors"])
    if approval.get("operator_approval_required") is not True:
        blockers.append("Operator approval record does not require approval.")
    if approval.get("operator_approval_granted") is not True:
        blockers.append("Operator approval has not been granted.")
    if approval.get("live_fetch_enabled_after_approval") is not True:
        blockers.append("Approval record does not enable live fetch after approval.")
    if fetch_plan.get("auth_required") is not False or fetch_plan.get("credentials_required") is not False:
        blockers.append("Fetch plan requires auth or credentials.")
    if fetch_plan.get("wallet_required") is not False:
        blockers.append("Fetch plan requires wallet access.")
    if fetch_plan.get("trading_endpoint_allowed") is not False:
        blockers.append("Fetch plan allows a trading endpoint.")
    if fetch_plan.get("order_endpoint_allowed") is not False:
        blockers.append("Fetch plan allows an order endpoint.")
    if fetch_plan.get("evidence_save_required") is not True:
        blockers.append("Evidence save is not required by the fetch plan.")
    if fetch_plan.get("replay_required_before_analysis_update") is not True:
        blockers.append("Saved evidence replay is not required before analysis update.")
    if fetch_plan.get("live_fetch_performed") is not False:
        blockers.append("Fetch plan indicates a live fetch already occurred.")
    if fetch_plan.get("scheduler_or_background_worker_allowed") is True:
        blockers.append("Scheduler or background worker is allowed by the plan.")
    requested_sources = fetch_plan.get("requested_sources", [])
    if isinstance(requested_sources, list) and isinstance(fetch_plan.get("max_request_count"), int):
        if len(requested_sources) > fetch_plan["max_request_count"]:
            blockers.append("Request count exceeds the max_request_count.")
    allowed_categories = {
        row["source_category"]
        for row in registry.get("allowed_sources", [])
        if isinstance(row, Mapping) and row.get("allowed") is True
    }
    for source in requested_sources if isinstance(requested_sources, list) else []:
        if not isinstance(source, Mapping):
            blockers.append("Requested source is not an object.")
            continue
        validation_row = validate_requested_source(source)
        if validation_row["blocked"]:
            blockers.append(f"Blocked source category requested: {validation_row['source_category']}")
        if validation_row["source_category"] not in allowed_categories:
            blockers.append(f"Source category is not in allowed registry: {validation_row['source_category']}")
        if source.get("auth_required") is True or source.get("credentials_required") is True:
            blockers.append(f"Requested source requires auth or credentials: {validation_row['source_id']}")
        if source.get("wallet_required") is True:
            blockers.append(f"Requested source requires wallet access: {validation_row['source_id']}")
        if source.get("trading_endpoint") is True or source.get("order_endpoint") is True:
            blockers.append(f"Requested source includes trading or order endpoint flags: {validation_row['source_id']}")
    if preview.get("live_fetch_allowed_now") is True:
        warnings.append("Dry-run preview unexpectedly marks live fetch as allowed now.")
    if safety_scan_report is not None and safety_scan_report.get("safety_ok") is not True:
        blockers.append("Safety scan did not pass.")
    required_next_actions = [
        "Review the fetch plan and source registry.",
        "Keep approval pending for this task.",
        "Create a separate approval packet before any future controlled public read-only request.",
        "Save evidence first and replay saved evidence before any analysis update.",
    ]
    ready = not blockers
    return {
        "contract_version": READINESS_GATE_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "fetch_plan_id": fetch_plan.get("fetch_plan_id", ""),
        "ready_for_controlled_public_fetch": ready,
        "blockers": blockers,
        "warnings": warnings,
        "required_next_actions": required_next_actions,
        "approval_status": {
            "operator_approval_required": approval.get("operator_approval_required") is True,
            "operator_approval_granted": approval.get("operator_approval_granted") is True,
            "live_fetch_enabled_after_approval": approval.get("live_fetch_enabled_after_approval") is True,
        },
        "gate_requirements": {
            "operator_approval_granted": approval.get("operator_approval_granted") is True,
            "allowed_source_categories_only": not any(
                "Blocked source category requested" in blocker or "not in allowed registry" in blocker
                for blocker in blockers
            ),
            "request_count_within_limit": len(fetch_plan.get("requested_sources", [])) <= fetch_plan.get("max_request_count", 0),
            "evidence_save_required": fetch_plan.get("evidence_save_required") is True,
            "replay_required_before_analysis_update": fetch_plan.get("replay_required_before_analysis_update") is True,
            "no_auth_wallet_trading_order_endpoint": not any(
                phrase in blocker
                for blocker in blockers
                for phrase in ("auth", "credentials", "wallet", "trading", "order")
            ),
            "no_scheduler_or_background_worker": fetch_plan.get("scheduler_or_background_worker_allowed") is not True,
            "no_live_fetch_already_performed": fetch_plan.get("live_fetch_performed") is False,
        },
        "live_network_used": False,
        "safety_summary": safe_summary(),
    }


def render_public_fetch_readiness_gate_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Public Fetch Readiness Gate",
        "",
        f"- Fetch plan ID: `{result.get('fetch_plan_id')}`",
        f"- Ready for controlled public fetch: `{str(result.get('ready_for_controlled_public_fetch')).lower()}`",
        "",
        "## Blockers",
        "",
        *bullet_lines(result.get("blockers", [])),
        "",
        "## Warnings",
        "",
        *bullet_lines(result.get("warnings", [])),
        "",
        "## Required Next Actions",
        "",
        *bullet_lines(result.get("required_next_actions", [])),
        "",
        "## Gate Requirements",
        "",
    ]
    for key, value in result.get("gate_requirements", {}).items():
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- Local readiness evaluation only.",
            "- No public request is made.",
            "- Readiness remains false in this task because approval is pending and live fetch is not enabled.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_public_fetch_readiness_gate(
    *,
    fetch_plan: Mapping[str, Any],
    approval: Mapping[str, Any],
    dry_run_preview: Mapping[str, Any] | None = None,
    source_registry: Mapping[str, Any] | None = None,
    safety_scan_report: Mapping[str, Any] | None = None,
    out_json_path: str | None = None,
    out_md_path: str | None = None,
) -> dict[str, Any]:
    result = evaluate_public_fetch_readiness(
        fetch_plan=fetch_plan,
        approval=approval,
        dry_run_preview=dry_run_preview,
        source_registry=source_registry,
        safety_scan_report=safety_scan_report,
    )
    if out_json_path is not None:
        write_json(out_json_path, result)
    if out_md_path is not None:
        write_text(out_md_path, render_public_fetch_readiness_gate_markdown(result))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate future controlled public read-only fetch readiness.")
    parser.add_argument("--fetch-plan", required=True, help="Input fetch plan JSON.")
    parser.add_argument("--approval", required=True, help="Input operator approval JSON.")
    parser.add_argument("--out-json", required=True, help="Output readiness gate JSON.")
    parser.add_argument("--out-md", required=True, help="Output readiness gate Markdown.")
    args = parser.parse_args(argv)
    fetch_plan = load_json_object(args.fetch_plan, label="fetch plan")
    approval = load_json_object(args.approval, label="operator approval")
    write_public_fetch_readiness_gate(
        fetch_plan=fetch_plan,
        approval=approval,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
