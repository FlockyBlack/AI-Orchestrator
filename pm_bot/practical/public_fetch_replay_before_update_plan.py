from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text

REPLAY_BEFORE_UPDATE_PLAN_CONTRACT_VERSION = "pmbot_public_fetch_replay_before_update_plan.v1"


def build_public_fetch_replay_before_update_plan(
    *,
    fetch_plan: Mapping[str, Any],
    request_manifest: Mapping[str, Any],
    evidence_save_plan: Mapping[str, Any],
) -> dict[str, Any]:
    request_intents = [
        intent for intent in request_manifest.get("request_intents", []) if isinstance(intent, Mapping)
    ]
    evidence_packet_inputs = [
        {
            "request_intent_id": intent.get("request_intent_id", ""),
            "market_id": intent.get("market_id", ""),
            "linked_hypothesis_id": intent.get("linked_hypothesis_id", ""),
            "expected_saved_packet": intent.get("save_evidence_as", ""),
        }
        for intent in request_intents
    ]
    affected_hypothesis_ids = sorted(
        {
            clean_text(intent.get("linked_hypothesis_id"))
            for intent in request_intents
            if clean_text(intent.get("linked_hypothesis_id"))
        }
    )
    fetch_plan_id = clean_text(fetch_plan.get("fetch_plan_id"))
    return {
        "contract_version": REPLAY_BEFORE_UPDATE_PLAN_CONTRACT_VERSION,
        "replay_plan_id": f"{fetch_plan_id}.replay_before_update_plan.006",
        "created_at": GENERATED_AT,
        "fetch_plan_id": fetch_plan_id,
        "request_manifest_id": request_manifest.get("request_manifest_id", ""),
        "evidence_save_plan_id": evidence_save_plan.get("evidence_save_plan_id", ""),
        "evidence_packet_inputs": evidence_packet_inputs,
        "affected_market_ids": list(fetch_plan.get("market_ids", [])),
        "affected_hypothesis_ids": affected_hypothesis_ids,
        "replay_adapter_required": True,
        "source_packet_mapping_required": True,
        "contradiction_check_required": True,
        "staleness_check_required": True,
        "operator_review_required_after_replay": True,
        "automatic_analysis_update_allowed": False,
        "automatic_trading_allowed": False,
        "live_fetch_performed": False,
        "live_network_used": False,
        "safety_summary": safe_summary(),
    }


def render_public_fetch_replay_before_update_plan_markdown(plan: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Public Fetch Replay Before Update Plan",
        "",
        f"- Replay plan ID: `{plan.get('replay_plan_id')}`",
        f"- Fetch plan ID: `{plan.get('fetch_plan_id')}`",
        f"- Request manifest ID: `{plan.get('request_manifest_id')}`",
        f"- Evidence save plan ID: `{plan.get('evidence_save_plan_id')}`",
        f"- Replay adapter required: `{str(plan.get('replay_adapter_required')).lower()}`",
        f"- Source packet mapping required: `{str(plan.get('source_packet_mapping_required')).lower()}`",
        f"- Automatic analysis update allowed: `{str(plan.get('automatic_analysis_update_allowed')).lower()}`",
        f"- Automatic trading allowed: `{str(plan.get('automatic_trading_allowed')).lower()}`",
        "",
        "## Evidence Packet Inputs",
        "",
    ]
    for row in plan.get("evidence_packet_inputs", []):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}`",
                f"  Market: `{row.get('market_id')}`",
                f"  Hypothesis: `{row.get('linked_hypothesis_id')}`",
                f"  Expected packet: `{row.get('expected_saved_packet')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Required Checks",
            "",
            f"- Contradiction check: `{str(plan.get('contradiction_check_required')).lower()}`",
            f"- Staleness check: `{str(plan.get('staleness_check_required')).lower()}`",
            f"- Operator review after replay: `{str(plan.get('operator_review_required_after_replay')).lower()}`",
            "",
            "## Affected Markets",
            "",
            *bullet_lines(f"`{market_id}`" for market_id in plan.get("affected_market_ids", [])),
            "",
            "## Safety Boundary",
            "",
            "- Saved evidence must be replayed before any PMBOT analysis update.",
            "- Replay does not update analysis automatically.",
            "- Trading remains blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_public_fetch_replay_before_update_plan(
    plan: Mapping[str, Any],
    *,
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    plan_dict = dict(plan)
    if out_json_path is not None:
        write_json(out_json_path, plan_dict)
    if out_md_path is not None:
        write_text(out_md_path, render_public_fetch_replay_before_update_plan_markdown(plan_dict))
    return plan_dict


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local-only replay-before-update plan.")
    parser.add_argument("--fetch-plan", required=True, help="Input fetch plan JSON.")
    parser.add_argument("--request-manifest", required=True, help="Input request manifest JSON.")
    parser.add_argument("--evidence-save-plan", required=True, help="Input evidence save plan JSON.")
    parser.add_argument("--out-json", required=True, help="Output replay plan JSON.")
    parser.add_argument("--out-md", required=True, help="Output replay plan Markdown.")
    args = parser.parse_args(argv)
    fetch_plan = load_json_object(args.fetch_plan, label="fetch plan")
    request_manifest = load_json_object(args.request_manifest, label="request manifest")
    evidence_save_plan = load_json_object(args.evidence_save_plan, label="evidence save plan")
    plan = build_public_fetch_replay_before_update_plan(
        fetch_plan=fetch_plan,
        request_manifest=request_manifest,
        evidence_save_plan=evidence_save_plan,
    )
    write_public_fetch_replay_before_update_plan(plan, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
