from __future__ import annotations

import argparse
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text
from pm_bot.practical.public_fetch_url_safety import validate_public_fetch_request_intent

EXECUTION_PREFLIGHT_CONTRACT_VERSION = "pmbot_public_fetch_execution_preflight.v1"
SCOPED_APPROVAL_CONTRACT_VERSION = "pmbot_scoped_public_read_only_fetch_approval.v1"
APPROVED_STATUS = "approved_for_scoped_public_read_only_fetch_only"
TASK_ID = "ORCH-PMBOT-PRACTICAL-007-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-OPERATOR-APPROVED"


def validate_scoped_operator_approval(approval: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    approved_scope = approval.get("approved_scope", {})
    if not isinstance(approved_scope, Mapping):
        blockers.append("approved_scope must be an object")
        approved_scope = {}
    if approval.get("contract_version") != SCOPED_APPROVAL_CONTRACT_VERSION:
        blockers.append("approval contract_version is not scoped public read-only approval v1")
    if approval.get("approval_for_task_id") != TASK_ID:
        blockers.append("approval_for_task_id does not match this task")
    if approval.get("approval_status") != APPROVED_STATUS:
        blockers.append("approval_status is not approved for scoped public read-only fetch only")
    if approval.get("approved_by") != "operator":
        blockers.append("approved_by must be operator")
    if not clean_text(approval.get("approved_at")):
        blockers.append("approved_at is required")
    if approval.get("expires_after_task") is not True:
        blockers.append("approval must expire after this task")
    if approval.get("reusable") is not False:
        blockers.append("approval must be non-reusable")

    expected_true = {
        "finite_public_read_only_fetch",
        "save_evidence_before_use",
        "replay_before_analysis_update",
        "no_authentication",
        "no_api_keys",
        "no_wallet",
        "no_orders",
        "no_trading",
        "no_scheduler",
        "no_background_worker",
        "no_browser_automation",
    }
    for key in sorted(expected_true):
        if approved_scope.get(key) is not True:
            blockers.append(f"approved_scope.{key} must be true")
    if approved_scope.get("max_request_count") != 5:
        blockers.append("approved_scope.max_request_count must be 5")
    approved_market_ids = {clean_text(market_id) for market_id in approved_scope.get("approved_market_ids", [])}
    required_market_ids = {"563650", "597964", "598936", "691547", "692258"}
    if approved_market_ids != required_market_ids:
        blockers.append("approved_scope.approved_market_ids must match the five PRACTICAL-004 markets")

    blocked_scope = " ".join(clean_text(item).lower() for item in approval.get("blocked_scope", []))
    for phrase in ("authenticated", "trading", "order", "wallet", "openrouter", "autonomous", "scheduler"):
        if phrase not in blocked_scope:
            warnings.append(f"blocked_scope does not mention {phrase}")
    return {"valid": not blockers, "blockers": blockers, "warnings": warnings}


def build_execution_preflight(
    *,
    approval: Mapping[str, Any],
    request_manifest: Mapping[str, Any],
    evidence_save_plan: Mapping[str, Any],
    replay_plan: Mapping[str, Any],
    fixture_mode: bool = False,
) -> dict[str, Any]:
    approval_validation = validate_scoped_operator_approval(approval)
    approved_scope = approval.get("approved_scope", {}) if isinstance(approval.get("approved_scope"), Mapping) else {}
    max_request_count = int(approved_scope.get("max_request_count") or 0)
    approved_market_ids = {clean_text(market_id) for market_id in approved_scope.get("approved_market_ids", [])}
    request_intents = [intent for intent in request_manifest.get("request_intents", []) if isinstance(intent, Mapping)]
    blockers = list(approval_validation["blockers"])
    warnings = list(approval_validation["warnings"])

    if request_manifest.get("contract_version") != "pmbot_public_fetch_request_manifest.v1":
        blockers.append("request manifest contract_version is invalid")
    if evidence_save_plan.get("evidence_save_required") is not True:
        blockers.append("evidence save plan does not require evidence save")
    if evidence_save_plan.get("replay_before_analysis_update") is not True:
        blockers.append("evidence save plan does not require replay before analysis update")
    if replay_plan.get("automatic_analysis_update_allowed") is not False:
        blockers.append("replay plan allows automatic analysis update")
    if replay_plan.get("automatic_trading_allowed") is not False:
        blockers.append("replay plan allows automatic trading")
    if len(request_intents) > max_request_count:
        blockers.append("request manifest count exceeds scoped approval max request count")

    executable: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for index, intent in enumerate(request_intents, start=1):
        validation = validate_public_fetch_request_intent(
            intent,
            request_index=index,
            max_request_count=max_request_count or 1,
            fixture_mode=fixture_mode,
        )
        intent_market = clean_text(intent.get("market_id"))
        if intent_market not in approved_market_ids:
            validation["allowed"] = False
            validation["blockers"].append("market_id is not included in scoped approval")
        row = {
            "request_intent_id": clean_text(intent.get("request_intent_id")),
            "market_id": intent_market,
            "source_category": clean_text(intent.get("source_category")),
            "source_reference": validation["sanitized_url_reference"],
            "url_safety": validation,
        }
        if validation["allowed"]:
            executable.append(row)
        else:
            blocked.append(row)
    if not executable:
        blockers.append("No executable public read-only request intents passed validation.")

    blockers = _dedupe(blockers)
    warnings = _dedupe(warnings)
    return {
        "contract_version": EXECUTION_PREFLIGHT_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "approval_id": approval.get("approval_id", ""),
        "approval_for_task_id": approval.get("approval_for_task_id", ""),
        "ready_to_execute_public_read_only_fetch": not blockers,
        "approved_request_count": len(executable),
        "blocked_request_count": len(blocked),
        "max_request_count": max_request_count,
        "executable_request_intents": executable,
        "blocked_request_intents": blocked,
        "blockers": blockers,
        "warnings": warnings,
        "approval_validation": approval_validation,
        "fixture_mode": fixture_mode,
        "safety_summary": safe_summary(),
    }


def render_execution_preflight_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Public Fetch Execution Preflight",
        "",
        f"- Ready to execute public read-only fetch: `{str(result.get('ready_to_execute_public_read_only_fetch')).lower()}`",
        f"- Approved executable requests: {result.get('approved_request_count')}",
        f"- Blocked requests: {result.get('blocked_request_count')}",
        f"- Max requests: {result.get('max_request_count')}",
        "",
        "## Blockers",
        "",
        *bullet_lines(result.get("blockers", [])),
        "",
        "## Warnings",
        "",
        *bullet_lines(result.get("warnings", [])),
        "",
        "## Executable Request Intents",
        "",
    ]
    for row in result.get("executable_request_intents", []):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}`",
                f"  Market: `{row.get('market_id')}`",
                f"  Source: `{row.get('source_reference')}`",
            ]
        )
    lines.extend(["", "## Blocked Request Intents", ""])
    for row in result.get("blocked_request_intents", []):
        safety = row.get("url_safety", {})
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}`",
                f"  Market: `{row.get('market_id')}`",
                f"  Source: `{row.get('source_reference')}`",
                f"  Blockers: {', '.join(safety.get('blockers', [])) or 'none'}",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- This preflight is local only and performs no network request.",
            "- Only explicit, scoped, public read-only GET intents may pass.",
            "- Evidence save and replay-before-update remain required.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_execution_preflight(
    *,
    approval: Mapping[str, Any],
    request_manifest: Mapping[str, Any],
    evidence_save_plan: Mapping[str, Any],
    replay_plan: Mapping[str, Any],
    out_json_path: str | None = None,
    out_md_path: str | None = None,
    fixture_mode: bool = False,
) -> dict[str, Any]:
    result = build_execution_preflight(
        approval=approval,
        request_manifest=request_manifest,
        evidence_save_plan=evidence_save_plan,
        replay_plan=replay_plan,
        fixture_mode=fixture_mode,
    )
    if out_json_path is not None:
        write_json(out_json_path, result)
    if out_md_path is not None:
        write_text(out_md_path, render_execution_preflight_markdown(result))
    return result


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    rows: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in seen:
            seen.add(text)
            rows.append(text)
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run PMBOT public fetch execution preflight.")
    parser.add_argument("--approval", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--evidence-save-plan", required=True)
    parser.add_argument("--replay-plan", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args(argv)
    write_execution_preflight(
        approval=load_json_object(args.approval, label="scoped approval"),
        request_manifest=load_json_object(args.manifest, label="request manifest"),
        evidence_save_plan=load_json_object(args.evidence_save_plan, label="evidence save plan"),
        replay_plan=load_json_object(args.replay_plan, label="replay plan"),
        out_json_path=args.out_json,
        out_md_path=args.out_md,
        fixture_mode=args.fixture_mode,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
