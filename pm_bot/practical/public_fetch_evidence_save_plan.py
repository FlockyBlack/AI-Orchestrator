from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text

EVIDENCE_SAVE_PLAN_CONTRACT_VERSION = "pmbot_public_fetch_evidence_save_plan.v1"

REQUIRED_EVIDENCE_METADATA_FIELDS = [
    "evidence_packet_id",
    "captured_at",
    "capture_mode",
    "source_id",
    "source_name",
    "source_category",
    "source_reference",
    "market_ids",
    "hypothesis_ids",
    "raw_excerpt_or_summary",
    "normalized_claims",
    "freshness_status",
    "contradiction_candidates",
    "limitations",
    "capture_errors",
    "auth_used",
    "credentials_used",
    "wallet_or_private_key_access",
    "orders_or_trading_actions",
    "safe_for_replay",
]


def build_public_fetch_evidence_save_plan(
    *,
    fetch_plan: Mapping[str, Any],
    evidence_directory: str = "pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence",
) -> dict[str, Any]:
    fetch_plan_id = clean_text(fetch_plan.get("fetch_plan_id"))
    return {
        "contract_version": EVIDENCE_SAVE_PLAN_CONTRACT_VERSION,
        "evidence_save_plan_id": f"{fetch_plan_id}.evidence_save_plan.006",
        "created_at": GENERATED_AT,
        "fetch_plan_id": fetch_plan_id,
        "market_ids": list(fetch_plan.get("market_ids", [])),
        "evidence_directory": evidence_directory,
        "filename_pattern": "{market_id}/{request_intent_id}.saved_public_evidence_packet.json",
        "required_metadata_fields": REQUIRED_EVIDENCE_METADATA_FIELDS,
        "raw_capture_policy": {
            "required": True,
            "description": "Save the public-source excerpt or concise capture summary before any replay.",
        },
        "normalized_claim_policy": {
            "required": True,
            "description": "Normalize captured public evidence into explicit claims before replay.",
        },
        "replay_before_analysis_update": True,
        "retention_policy": "retain_with_task_artifacts_until_operator_reviewed_cleanup",
        "overwrite_policy": "no_overwrite",
        "redaction_policy": "If credential, session, wallet, or private material appears unexpectedly, block use and require separate local review.",
        "safety_flags_required": {
            "auth_used": False,
            "credentials_used": False,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "safe_for_replay": True,
            "capture_context_must_be_explicit": True,
        },
        "validation_required_before_use": True,
        "evidence_save_required": True,
        "live_fetch_performed": False,
        "live_network_used": False,
        "safety_summary": safe_summary(),
    }


def render_public_fetch_evidence_save_plan_markdown(plan: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Public Fetch Evidence Save Plan",
        "",
        f"- Evidence save plan ID: `{plan.get('evidence_save_plan_id')}`",
        f"- Fetch plan ID: `{plan.get('fetch_plan_id')}`",
        f"- Evidence directory: `{plan.get('evidence_directory')}`",
        f"- Filename pattern: `{plan.get('filename_pattern')}`",
        f"- Overwrite policy: `{plan.get('overwrite_policy')}`",
        f"- Replay before analysis update: `{str(plan.get('replay_before_analysis_update')).lower()}`",
        f"- Validation required before use: `{str(plan.get('validation_required_before_use')).lower()}`",
        "",
        "## Required Metadata",
        "",
        *bullet_lines(f"`{field}`" for field in plan.get("required_metadata_fields", [])),
        "",
        "## Capture Policy",
        "",
        f"- Raw capture required: `{str(plan.get('raw_capture_policy', {}).get('required')).lower()}`",
        f"- Normalized claims required: `{str(plan.get('normalized_claim_policy', {}).get('required')).lower()}`",
        f"- Retention: {plan.get('retention_policy')}",
        f"- Redaction: {plan.get('redaction_policy')}",
        "",
        "## Safety Flags",
        "",
    ]
    for key, value in plan.get("safety_flags_required", {}).items():
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- Evidence must be saved before replay.",
            "- Saved evidence must validate before use.",
            "- This plan performs no public fetch.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_public_fetch_evidence_save_plan(
    plan: Mapping[str, Any],
    *,
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    plan_dict = dict(plan)
    if out_json_path is not None:
        write_json(out_json_path, plan_dict)
    if out_md_path is not None:
        write_text(out_md_path, render_public_fetch_evidence_save_plan_markdown(plan_dict))
    return plan_dict


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local-only public fetch evidence save plan.")
    parser.add_argument("--fetch-plan", required=True, help="Input fetch plan JSON.")
    parser.add_argument("--out-json", required=True, help="Output evidence save plan JSON.")
    parser.add_argument("--out-md", required=True, help="Output evidence save plan Markdown.")
    args = parser.parse_args(argv)
    fetch_plan = load_json_object(args.fetch_plan, label="fetch plan")
    plan = build_public_fetch_evidence_save_plan(fetch_plan=fetch_plan)
    write_public_fetch_evidence_save_plan(plan, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
