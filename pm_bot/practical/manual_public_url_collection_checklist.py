from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.new_market_public_source_candidates import GENERATED_AT_017, NEW_MARKET_ID, NEW_MARKET_TITLE
from pm_bot.practical.practical_io import bullet_lines, clean_text, safe_summary, write_json, write_text

CHECKLIST_CONTRACT_VERSION = "pmbot_manual_public_url_collection_checklist.v1"

DEFAULT_CHECKLIST_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "check_id": "public_http_url",
        "label": "must be public HTTP(S)",
        "required": True,
        "operator_check": "Use a normal http or https page that can be opened without credentials.",
    },
    {
        "check_id": "no_login",
        "label": "must not require login",
        "required": True,
        "operator_check": "Do not use pages behind accounts, KYC, paywalls, or identity gates.",
    },
    {
        "check_id": "no_api_key",
        "label": "must not require API key",
        "required": True,
        "operator_check": "Do not use URLs that depend on tokens, API keys, signatures, or private headers.",
    },
    {
        "check_id": "no_cookies",
        "label": "must not require cookies",
        "required": True,
        "operator_check": "Do not use browser-session URLs or profile-specific links.",
    },
    {
        "check_id": "no_wallet_or_execution_endpoint",
        "label": "must not be wallet, order, or trading endpoint",
        "required": True,
        "operator_check": "Use read-only public reference pages only.",
    },
    {
        "check_id": "no_private_dashboard",
        "label": "must not be a private dashboard",
        "required": True,
        "operator_check": "Avoid private dashboards, admin pages, local tools, and account-specific views.",
    },
    {
        "check_id": "no_local_or_internal_host",
        "label": "must not be localhost or internal IP",
        "required": True,
        "operator_check": "Do not use localhost, private IP ranges, internal hostnames, or intranet links.",
    },
    {
        "check_id": "official_or_high_quality",
        "label": "should be official or high-quality public reference",
        "required": False,
        "operator_check": "Prefer official market, resolution, benchmark, or durable public reference pages.",
    },
    {
        "check_id": "maps_to_expected_evidence",
        "label": "should map clearly to expected evidence type",
        "required": False,
        "operator_check": "The URL should visibly support the evidence type named in the packet row.",
    },
    {
        "check_id": "stable_for_replay",
        "label": "should be stable enough for future replay",
        "required": False,
        "operator_check": "Prefer durable pages over ephemeral search results, interactive state, or personalized views.",
    },
)


def build_url_collection_validation_checklist(
    *,
    market_id: str = NEW_MARKET_ID,
    market_title: str = NEW_MARKET_TITLE,
    source_missing_url_items: Sequence[Mapping[str, Any]] = (),
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    return {
        "contract_version": CHECKLIST_CONTRACT_VERSION,
        "checklist_id": f"manual-url-collection-checklist-017b-{clean_text(market_id)}",
        "generated_at": generated_at,
        "market_id": clean_text(market_id),
        "market_title": clean_text(market_title),
        "checklist_items": [dict(row) for row in DEFAULT_CHECKLIST_ITEMS],
        "source_category_checklist": [
            {
                "item_id": clean_text(row.get("request_intent_id") or row.get("candidate_source_id") or row.get("item_id")),
                "source_category": clean_text(row.get("source_category")),
                "source_name": clean_text(row.get("source_name_or_placeholder") or row.get("source_name")),
                "expected_evidence_type": clean_text(row.get("expected_evidence_type")),
                "operator_goal": "Find one concrete public URL that matches this evidence type and passes the checklist.",
            }
            for row in source_missing_url_items
            if isinstance(row, Mapping)
        ],
        "operator_fill_target": "manual_public_url_collection_packet_573656.json",
        "live_fetch_performed": False,
        "no_real_trade_decision": True,
        "safety_summary": _checklist_safety_summary(),
    }


def render_url_collection_validation_checklist_markdown(checklist: Mapping[str, Any]) -> str:
    lines = [
        "# Manual URL Collection Validation Checklist 573656",
        "",
        f"- Market: `{checklist.get('market_id')}` {checklist.get('market_title')}",
        f"- Fill target: `{checklist.get('operator_fill_target')}`",
        f"- Live fetch performed: `{str(checklist.get('live_fetch_performed')).lower()}`",
        "",
        "## Required URL Checks",
        "",
    ]
    for row in checklist.get("checklist_items", []):
        if not isinstance(row, Mapping):
            continue
        marker = "required" if row.get("required") is True else "preferred"
        lines.extend(
            [
                f"- `{row.get('check_id')}` {row.get('label')} ({marker})",
                f"  Operator check: {row.get('operator_check')}",
            ]
        )
    lines.extend(["", "## Missing Source Rows", ""])
    for row in checklist.get("source_category_checklist", []):
        if not isinstance(row, Mapping):
            continue
        lines.extend(
            [
                f"- `{row.get('source_category')}` {row.get('source_name')}",
                f"  Evidence type: {row.get('expected_evidence_type')}",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- This checklist is local guidance only.",
            "- No URL is fetched, approved, or treated as evidence by this artifact.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_url_collection_validation_checklist(
    *,
    out_json_path: str | Path,
    out_md_path: str | Path,
    market_id: str = NEW_MARKET_ID,
    market_title: str = NEW_MARKET_TITLE,
    source_missing_url_items: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    checklist = build_url_collection_validation_checklist(
        market_id=market_id,
        market_title=market_title,
        source_missing_url_items=source_missing_url_items,
    )
    write_json(out_json_path, checklist)
    write_text(out_md_path, render_url_collection_validation_checklist_markdown(checklist))
    return checklist


def _checklist_safety_summary() -> dict[str, Any]:
    summary = safe_summary()
    summary.update(
        {
            "new_live_fetch_performed": False,
            "new_polymarket_api_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "outcome_resolution_invented": False,
            "no_scheduler_daemon_background_worker": True,
            "no_autonomous_trading": True,
        }
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the manual public URL collection checklist.")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args(argv)
    write_url_collection_validation_checklist(out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
