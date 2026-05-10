from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import (
    GENERATED_AT,
    bullet_lines,
    clean_text,
    load_json_object,
    safe_summary,
    slug_id,
    write_json,
    write_text,
)
from pm_bot.practical.public_source_registry import blocked_source_categories, validate_source_category

REQUEST_MANIFEST_CONTRACT_VERSION = "pmbot_public_fetch_request_manifest.v1"


def build_public_fetch_request_manifest(
    *,
    fetch_plan: Mapping[str, Any],
    link_map: Mapping[str, Any] | None = None,
    evidence_directory: str = "pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence",
) -> dict[str, Any]:
    hypothesis_by_market = _hypothesis_by_market(link_map or {})
    request_intents = [
        _request_intent(
            index=index,
            source=source,
            fetch_plan_id=clean_text(fetch_plan.get("fetch_plan_id")),
            fallback_hypothesis_id=hypothesis_by_market.get(clean_text(source.get("market_id")), ""),
            evidence_directory=evidence_directory,
        )
        for index, source in enumerate(fetch_plan.get("requested_sources", []), start=1)
        if isinstance(source, Mapping)
    ]
    return {
        "contract_version": REQUEST_MANIFEST_CONTRACT_VERSION,
        "request_manifest_id": f"{clean_text(fetch_plan.get('fetch_plan_id'))}.request_manifest.006",
        "created_at": GENERATED_AT,
        "fetch_plan_id": clean_text(fetch_plan.get("fetch_plan_id")),
        "market_ids": list(fetch_plan.get("market_ids", [])),
        "market_count": len(fetch_plan.get("market_ids", [])),
        "request_intent_count": len(request_intents),
        "max_request_count": fetch_plan.get("max_request_count"),
        "request_intents": request_intents,
        "blocked_source_categories": blocked_source_categories(),
        "manifest_only": True,
        "live_fetch_performed": False,
        "live_network_used": False,
        "safety_summary": safe_summary(),
    }


def render_public_fetch_request_manifest_markdown(manifest: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Public Fetch Request Manifest",
        "",
        f"- Manifest ID: `{manifest.get('request_manifest_id')}`",
        f"- Fetch plan ID: `{manifest.get('fetch_plan_id')}`",
        f"- Markets: {manifest.get('market_count')}",
        f"- Request intents: {manifest.get('request_intent_count')}",
        f"- Max requests: {manifest.get('max_request_count')}",
        f"- Manifest only: `{str(manifest.get('manifest_only')).lower()}`",
        f"- Live fetch performed: `{str(manifest.get('live_fetch_performed')).lower()}`",
        "",
        "## Request Intents",
        "",
    ]
    for intent in manifest.get("request_intents", []):
        lines.extend(
            [
                f"- `{intent.get('request_intent_id')}`",
                f"  Market: `{intent.get('market_id')}` {intent.get('market_title')}",
                f"  Source category: `{intent.get('source_category')}`",
                f"  Source: {intent.get('source_name_or_placeholder')}",
                f"  Evidence: {intent.get('expected_evidence_type')}",
                f"  Allowed by registry: `{str(intent.get('allowed_by_registry')).lower()}`",
                f"  Save evidence as: `{intent.get('save_evidence_as')}`",
            ]
        )
        if intent.get("blocked_reason"):
            lines.append(f"  Blocked reason: {intent.get('blocked_reason')}")
    lines.extend(
        [
            "",
            "## Blocked Source Categories",
            "",
            *bullet_lines(f"`{category}`" for category in manifest.get("blocked_source_categories", [])),
            "",
            "## Safety Boundary",
            "",
            "- This is a request-intent manifest only.",
            "- No public source is contacted.",
            "- Auth, wallet, signing, orders, trading paths, schedulers, and polling remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_public_fetch_request_manifest(
    manifest: Mapping[str, Any],
    *,
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    manifest_dict = dict(manifest)
    if out_json_path is not None:
        write_json(out_json_path, manifest_dict)
    if out_md_path is not None:
        write_text(out_md_path, render_public_fetch_request_manifest_markdown(manifest_dict))
    return manifest_dict


def _request_intent(
    *,
    index: int,
    source: Mapping[str, Any],
    fetch_plan_id: str,
    fallback_hypothesis_id: str,
    evidence_directory: str,
) -> dict[str, Any]:
    market_id = clean_text(source.get("market_id"))
    source_id = clean_text(source.get("source_id") or source.get("planned_source_id") or source.get("source_category"))
    category = clean_text(source.get("source_category"))
    validation = validate_source_category(category)
    request_intent_id = f"public_fetch_request_intent_006_{index:02d}_{market_id}_{slug_id(source_id)}"
    requires_auth = source.get("auth_required") is True or source.get("credentials_required") is True
    trading_or_order_endpoint = source.get("trading_endpoint") is True or source.get("order_endpoint") is True
    wallet_or_signing_required = source.get("wallet_required") is True or source.get("wallet_or_signing_required") is True
    blocked_reasons = []
    if validation["blocked"]:
        blocked_reasons.append(validation["reason"])
    if requires_auth:
        blocked_reasons.append("Source intent requires auth or credentials.")
    if trading_or_order_endpoint:
        blocked_reasons.append("Source intent points at trading or order behavior.")
    if wallet_or_signing_required:
        blocked_reasons.append("Source intent requires wallet or signing access.")
    return {
        "request_intent_id": request_intent_id,
        "market_id": market_id,
        "market_title": clean_text(source.get("market_title")),
        "source_category": category,
        "source_name_or_placeholder": clean_text(source.get("source_name")),
        "source_reference_or_placeholder": clean_text(source.get("source_reference")),
        "reason_needed": clean_text(source.get("why_fresh_evidence_would_matter")),
        "expected_evidence_type": clean_text(source.get("expected_evidence_type")),
        "linked_hypothesis_id": clean_text(source.get("hypothesis_id") or fallback_hypothesis_id),
        "save_evidence_as": f"{evidence_directory}/{market_id}/{request_intent_id}.saved_public_evidence_packet.json",
        "allowed_by_registry": validation["allowed"] and not blocked_reasons,
        "blocked_reason": " ".join(blocked_reasons),
        "requires_auth": requires_auth,
        "trading_or_order_endpoint": trading_or_order_endpoint,
        "wallet_or_signing_required": wallet_or_signing_required,
        "live_fetch_performed": False,
        "source_plan_id": fetch_plan_id,
    }


def _hypothesis_by_market(link_map: Mapping[str, Any]) -> dict[str, str]:
    rows: dict[str, str] = {}
    for link in link_map.get("links", []):
        if isinstance(link, Mapping):
            market_id = clean_text(link.get("market_id"))
            hypothesis_id = clean_text(link.get("hypothesis_id"))
            if market_id and hypothesis_id:
                rows[market_id] = hypothesis_id
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local-only public fetch request-intent manifest.")
    parser.add_argument("--fetch-plan", required=True, help="Input fetch plan JSON.")
    parser.add_argument("--link-map", default=None, help="Optional fetch-plan-to-hypotheses link map JSON.")
    parser.add_argument("--out-json", required=True, help="Output manifest JSON.")
    parser.add_argument("--out-md", required=True, help="Output manifest Markdown.")
    args = parser.parse_args(argv)
    fetch_plan = load_json_object(args.fetch_plan, label="fetch plan")
    link_map = load_json_object(args.link_map, label="link map") if args.link_map else None
    manifest = build_public_fetch_request_manifest(fetch_plan=fetch_plan, link_map=link_map)
    write_public_fetch_request_manifest(manifest, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
