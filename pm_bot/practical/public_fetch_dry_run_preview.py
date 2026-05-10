from __future__ import annotations

import argparse
from collections import Counter
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, load_json_object, safe_summary, sorted_counter_dict, write_json, write_text
from pm_bot.practical.public_read_only_fetch_contract import assert_valid_fetch_plan, validate_fetch_plan
from pm_bot.practical.public_source_registry import validate_requested_source

DRY_RUN_PREVIEW_CONTRACT_VERSION = "pmbot_public_read_only_fetch_dry_run_preview.v1"


def build_fetch_dry_run_preview(fetch_plan: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_fetch_plan(fetch_plan)
    category_counts: Counter[str] = Counter()
    evidence_counts: Counter[str] = Counter()
    affected_markets: dict[str, dict[str, str]] = {}
    safety_blockers = []
    for source in fetch_plan.get("requested_sources", []):
        if not isinstance(source, Mapping):
            continue
        category = str(source.get("source_category", "")).strip()
        evidence_type = str(source.get("expected_evidence_type", "")).strip() or "unspecified"
        category_counts[category] += 1
        evidence_counts[evidence_type] += 1
        market_id = str(source.get("market_id", "")).strip()
        if market_id:
            affected_markets[market_id] = {
                "market_id": market_id,
                "market_title": str(source.get("market_title", "")).strip(),
            }
        source_validation = validate_requested_source(source)
        if source_validation["blocked"]:
            safety_blockers.append(
                f"Blocked source category in planned source {source_validation['source_id']}: {source_validation['source_category']}"
            )
    if not validation["valid"]:
        safety_blockers.extend(validation["errors"])
    if fetch_plan.get("operator_approval_granted") is not True:
        safety_blockers.append("Operator approval is not granted.")
    safety_blockers.append("Live fetch is not part of this task.")
    preview = {
        "contract_version": DRY_RUN_PREVIEW_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "fetch_plan_id": fetch_plan.get("fetch_plan_id", ""),
        "request_count": len(fetch_plan.get("requested_sources", [])),
        "max_request_count": fetch_plan.get("max_request_count"),
        "markets_affected": sorted(affected_markets.values(), key=lambda row: row["market_id"]),
        "source_category_counts": sorted_counter_dict(category_counts),
        "evidence_expected_counts": sorted_counter_dict(evidence_counts),
        "safety_blockers": safety_blockers,
        "approval_status": {
            "operator_approval_required": fetch_plan.get("operator_approval_required") is True,
            "operator_approval_granted": fetch_plan.get("operator_approval_granted") is True,
        },
        "live_fetch": {
            "allowed_now": False,
            "reason": "Operator approval is not granted and live fetch is not part of this task.",
        },
        "live_fetch_allowed_now": False,
        "live_network_used": False,
        "safety_summary": safe_summary(),
    }
    return preview


def render_fetch_dry_run_preview_markdown(preview: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Public Fetch Dry-Run Preview",
        "",
        f"- Fetch plan ID: `{preview.get('fetch_plan_id')}`",
        f"- Planned requests: {preview.get('request_count')}",
        f"- Max requests: {preview.get('max_request_count')}",
        f"- Live fetch allowed now: `{str(preview.get('live_fetch_allowed_now')).lower()}`",
        f"- Reason: {preview.get('live_fetch', {}).get('reason')}",
        "",
        "## Markets Affected",
        "",
        *bullet_lines(
            f"`{row['market_id']}` {row['market_title']}" for row in preview.get("markets_affected", [])
        ),
        "",
        "## Source Categories",
        "",
        *bullet_lines(
            f"`{category}`: {count}" for category, count in preview.get("source_category_counts", {}).items()
        ),
        "",
        "## Evidence Expected",
        "",
        *bullet_lines(
            f"`{evidence_type}`: {count}" for evidence_type, count in preview.get("evidence_expected_counts", {}).items()
        ),
        "",
        "## Safety Blockers",
        "",
        *bullet_lines(preview.get("safety_blockers", [])),
        "",
        "## Safety Boundary",
        "",
        "- Dry-run preview only.",
        "- No network request is made.",
        "- Approval remains pending.",
    ]
    return "\n".join(lines) + "\n"


def write_fetch_dry_run_preview(
    *,
    fetch_plan: Mapping[str, Any],
    out_json_path: str | None = None,
    out_md_path: str | None = None,
) -> dict[str, Any]:
    assert_valid_fetch_plan(fetch_plan)
    preview = build_fetch_dry_run_preview(fetch_plan)
    if out_json_path is not None:
        write_json(out_json_path, preview)
    if out_md_path is not None:
        write_text(out_md_path, render_fetch_dry_run_preview_markdown(preview))
    return preview


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local-only dry-run preview for a public read-only fetch plan.")
    parser.add_argument("--fetch-plan", required=True, help="Input fetch plan JSON.")
    parser.add_argument("--out-json", required=True, help="Output dry-run preview JSON.")
    parser.add_argument("--out-md", required=True, help="Output dry-run preview Markdown.")
    args = parser.parse_args(argv)
    plan = load_json_object(args.fetch_plan, label="fetch plan")
    write_fetch_dry_run_preview(fetch_plan=plan, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
