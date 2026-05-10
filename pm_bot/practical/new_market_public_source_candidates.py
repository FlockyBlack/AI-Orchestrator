from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from pm_bot.practical.practical_io import (
    bullet_lines,
    clean_text,
    load_json_object,
    safe_summary,
    write_json,
    write_text,
)
from pm_bot.practical.public_source_registry import validate_source_category

SOURCE_CANDIDATES_CONTRACT_VERSION = "pmbot_new_market_public_source_candidates.v1"
MANUAL_URL_MAPPING_FIXTURE_CONTRACT_VERSION = "pmbot_new_market_public_url_mapping_manual_fixture.v1"

GENERATED_AT_017 = "2026-05-11T00:00:00Z"
NEW_MARKET_ID = "573656"
NEW_MARKET_TITLE = "Will Bitcoin hit $150k by December 31, 2026?"
NEW_MARKET_HYPOTHESIS_ID = "573656.analysis.ceab64191597.paper_hypothesis"
DEFAULT_NORMALIZED_INPUT_PATH = Path("pm_bot/practical/artifacts/add_market_016/normalized_input_016.json")

CANDIDATE_SOURCE_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "candidate_source_key": "public_market_metadata_page_reference",
        "source_category": "public_market_metadata_endpoint_placeholder",
        "source_name": "public market metadata page/reference",
        "expected_evidence_type": "public market metadata, rules, status, and linked reference snapshot",
        "expected_evidence_role": "Confirm the saved local title, rules, and public resolution references before any future evidence replay.",
        "include_in_manifest": True,
    },
    {
        "candidate_source_key": "public_bitcoin_price_reference_category",
        "source_category": "public_static_web_page_placeholder",
        "source_name": "public Bitcoin price reference category",
        "expected_evidence_type": "public Bitcoin price threshold reference snapshot",
        "expected_evidence_role": "Capture the public price reference category that would later support threshold and timestamp review.",
        "include_in_manifest": True,
    },
    {
        "candidate_source_key": "public_resolution_source_reference_category",
        "source_category": "public_resolution_source_page_placeholder",
        "source_name": "public resolution source reference category",
        "expected_evidence_type": "public resolution rules or resolution-source reference snapshot",
        "expected_evidence_role": "Confirm the public source used for resolving whether the threshold condition was met.",
        "include_in_manifest": True,
    },
    {
        "candidate_source_key": "public_crypto_market_data_reference_category",
        "source_category": "public_static_web_page_placeholder",
        "source_name": "public crypto market data reference category",
        "expected_evidence_type": "public crypto market data reference snapshot",
        "expected_evidence_role": "Provide a public market data source category for later operator-reviewed evidence collection.",
        "include_in_manifest": False,
    },
    {
        "candidate_source_key": "public_exchange_index_reference_category",
        "source_category": "public_static_web_page_placeholder",
        "source_name": "public exchange/index reference category",
        "expected_evidence_type": "public exchange or index reference snapshot",
        "expected_evidence_role": "Provide a public exchange or index source category if the market rules name one later.",
        "include_in_manifest": False,
    },
    {
        "candidate_source_key": "public_source_already_present_in_normalized_input",
        "source_category": "public_static_web_page_placeholder",
        "source_name": "public source already present in normalized input",
        "expected_evidence_type": "locally present source reference review",
        "expected_evidence_role": "Check whether the normalized input already contains concrete public HTTP(S) URLs.",
        "include_in_manifest": False,
    },
)


def build_new_market_public_source_candidates(
    *,
    normalized_input: Mapping[str, Any] | None = None,
    manual_url_mapping_fixture: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    normalized_input = normalized_input or load_json_object(DEFAULT_NORMALIZED_INPUT_PATH, label="normalized input")
    fixture_rows = _fixture_rows(manual_url_mapping_fixture or {})
    local_urls = _local_concrete_public_urls(normalized_input)
    market_id = clean_text(normalized_input.get("market_id") or NEW_MARKET_ID)
    market_title = clean_text(normalized_input.get("market_title") or NEW_MARKET_TITLE)

    candidate_sources: list[dict[str, Any]] = []
    for index, template in enumerate(CANDIDATE_SOURCE_TEMPLATES, start=1):
        category = clean_text(template["source_category"])
        source_name = clean_text(template["source_name"])
        validation = validate_source_category(category)
        fixture_row = _matching_fixture_row(fixture_rows, market_id, category, source_name)
        fixture_url = _optional_text((fixture_row or {}).get("concrete_public_url"))
        fixture_status = _optional_text((fixture_row or {}).get("url_status"))
        local_url = local_urls[0] if source_name == "public source already present in normalized input" and local_urls else ""
        concrete_url = fixture_url or local_url
        url_status = "concrete_safe_public_url" if concrete_url else "missing"
        if fixture_status == "blocked" or validation["blocked"]:
            url_status = "blocked"
        candidate_sources.append(
            {
                "candidate_source_id": f"new-market-017:{market_id}:{index:02d}:{template['candidate_source_key']}",
                "candidate_source_key": template["candidate_source_key"],
                "market_id": market_id,
                "market_title": market_title,
                "source_category": category,
                "source_name": source_name,
                "source_reference_or_placeholder": concrete_url
                or f"public_source_placeholder:{category}:{market_id}:{template['candidate_source_key']}",
                "concrete_public_url": concrete_url or None,
                "url_status": url_status,
                "allowed_by_registry": validation["allowed"] and url_status != "blocked",
                "blocked": url_status == "blocked",
                "reason": _optional_text((fixture_row or {}).get("reason")) or _default_reason(url_status),
                "expected_evidence_type": _optional_text((fixture_row or {}).get("expected_evidence_type"))
                or clean_text(template["expected_evidence_type"]),
                "expected_evidence_role": clean_text(template["expected_evidence_role"]),
                "linked_hypothesis_id": _optional_text((fixture_row or {}).get("linked_hypothesis_id"))
                or NEW_MARKET_HYPOTHESIS_ID,
                "include_in_manifest": template["include_in_manifest"] is True,
                "requires_auth": False,
                "credentials_required": False,
                "cookies_required": False,
                "wallet_or_signing_required": False,
                "trading_or_order_endpoint": False,
                "live_fetch_performed": False,
                "source_category_validation": validation,
            }
        )

    safe_sources = [row for row in candidate_sources if row["allowed_by_registry"] and row["url_status"] != "blocked"]
    missing = [row for row in safe_sources if row["url_status"] == "missing"]
    blocked = [row for row in candidate_sources if row["url_status"] == "blocked"]
    return {
        "contract_version": SOURCE_CANDIDATES_CONTRACT_VERSION,
        "generated_at": generated_at,
        "market_id": market_id,
        "market_title": market_title,
        "candidate_sources": candidate_sources,
        "safe_source_categories": sorted({row["source_category"] for row in safe_sources}),
        "missing_concrete_urls": [
            {
                "candidate_source_id": row["candidate_source_id"],
                "source_category": row["source_category"],
                "source_name": row["source_name"],
                "reason": row["reason"],
                "include_in_manifest": row["include_in_manifest"],
            }
            for row in missing
        ],
        "blocked_source_categories": [
            {
                "candidate_source_id": row["candidate_source_id"],
                "source_category": row["source_category"],
                "source_name": row["source_name"],
                "reason": row["reason"],
            }
            for row in blocked
        ],
        "source_selection_notes": [
            "Candidate sources are category placeholders unless a concrete public URL is already present locally.",
            "The normalized input contains source placeholders and search phrases, not concrete public HTTP(S) URLs.",
            "The first future fetch manifest is capped at three request intents.",
            "Operator approval remains required before any future public read-only request.",
        ],
        "no_live_fetch_performed": True,
        "live_fetch_performed": False,
        "safety_summary": _source_candidate_safety_summary(),
    }


def build_manual_url_mapping_fixture(
    *,
    source_candidates: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    source_candidates = source_candidates or build_new_market_public_source_candidates()
    mappings = []
    for row in source_candidates.get("candidate_sources", []):
        if not isinstance(row, Mapping) or row.get("include_in_manifest") is not True:
            continue
        mappings.append(
            {
                "market_id": clean_text(row.get("market_id")),
                "market_title": clean_text(row.get("market_title")),
                "source_category": clean_text(row.get("source_category")),
                "source_name": clean_text(row.get("source_name")),
                "concrete_public_url": row.get("concrete_public_url"),
                "url_status": clean_text(row.get("url_status")),
                "reason": clean_text(row.get("reason")),
                "expected_evidence_type": clean_text(row.get("expected_evidence_type")),
                "linked_hypothesis_id": clean_text(row.get("linked_hypothesis_id")),
                "live_fetch_performed": False,
            }
        )
    return {
        "contract_version": MANUAL_URL_MAPPING_FIXTURE_CONTRACT_VERSION,
        "generated_at": generated_at,
        "market_id": clean_text(source_candidates.get("market_id") or NEW_MARKET_ID),
        "market_title": clean_text(source_candidates.get("market_title") or NEW_MARKET_TITLE),
        "mappings": mappings,
        "fixture_notes": [
            "Manual fixture created locally for PRACTICAL-017.",
            "Concrete public URLs are intentionally null because none were already present locally.",
            "Do not fetch these sources until a later separately approved task.",
        ],
        "live_fetch_performed": False,
        "safety_summary": _source_candidate_safety_summary(),
    }


def render_new_market_public_source_candidates_markdown(candidates: Mapping[str, Any]) -> str:
    lines = [
        "# New Market Public Source Candidates 017",
        "",
        f"- Market: `{candidates.get('market_id')}` {candidates.get('market_title')}",
        f"- Candidate sources: {len(candidates.get('candidate_sources', []))}",
        f"- Missing concrete URLs: {len(candidates.get('missing_concrete_urls', []))}",
        f"- Blocked source categories: {len(candidates.get('blocked_source_categories', []))}",
        f"- Live fetch performed: `{str(candidates.get('live_fetch_performed')).lower()}`",
        "",
        "## Candidate Sources",
        "",
    ]
    for row in candidates.get("candidate_sources", []):
        if not isinstance(row, Mapping):
            continue
        lines.extend(
            [
                f"- `{row.get('candidate_source_key')}` `{row.get('source_category')}`",
                f"  Name: {row.get('source_name')}",
                f"  URL status: `{row.get('url_status')}`",
                f"  Include in capped manifest: `{str(row.get('include_in_manifest')).lower()}`",
                f"  Evidence type: {row.get('expected_evidence_type')}",
            ]
        )
    lines.extend(
        [
            "",
            "## Source Selection Notes",
            "",
            *bullet_lines(str(item) for item in candidates.get("source_selection_notes", [])),
            "",
            "## Safety Boundary",
            "",
            "- Local source-category planning only.",
            "- No source is contacted and no public URL is fetched.",
            "- No auth, API key, cookie, wallet, order, trading, scheduler, or background worker is used.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_manual_url_mapping_fixture_markdown(fixture: Mapping[str, Any]) -> str:
    lines = [
        "# New Market Manual URL Mapping Fixture 017",
        "",
        f"- Market: `{fixture.get('market_id')}` {fixture.get('market_title')}",
        f"- Mappings: {len(fixture.get('mappings', []))}",
        f"- Live fetch performed: `{str(fixture.get('live_fetch_performed')).lower()}`",
        "",
        "## Mappings",
        "",
    ]
    for row in fixture.get("mappings", []):
        if not isinstance(row, Mapping):
            continue
        lines.extend(
            [
                f"- `{row.get('source_category')}` {row.get('source_name')}",
                f"  URL status: `{row.get('url_status')}`",
                f"  Concrete public URL: `{row.get('concrete_public_url')}`",
                f"  Reason: {row.get('reason')}",
            ]
        )
    lines.extend(["", "## Notes", "", *bullet_lines(str(item) for item in fixture.get("fixture_notes", []))])
    return "\n".join(lines) + "\n"


def write_new_market_public_source_candidates(
    *,
    out_json_path: str | Path,
    out_md_path: str | Path,
    fixture_json_path: str | Path | None = None,
    fixture_md_path: str | Path | None = None,
    normalized_input_path: str | Path = DEFAULT_NORMALIZED_INPUT_PATH,
) -> dict[str, Any]:
    normalized_input = load_json_object(normalized_input_path, label="normalized input")
    candidates = build_new_market_public_source_candidates(normalized_input=normalized_input)
    write_json(out_json_path, candidates)
    write_text(out_md_path, render_new_market_public_source_candidates_markdown(candidates))
    if fixture_json_path is not None:
        fixture = build_manual_url_mapping_fixture(source_candidates=candidates)
        write_json(fixture_json_path, fixture)
        if fixture_md_path is not None:
            write_text(fixture_md_path, render_manual_url_mapping_fixture_markdown(fixture))
    return candidates


def _source_candidate_safety_summary() -> dict[str, Any]:
    summary = safe_summary()
    summary.update(
        {
            "new_live_fetch_performed": False,
            "new_polymarket_api_calls_performed": 0,
            "outcome_resolution_invented": False,
            "no_scheduler_daemon_background_worker": True,
            "no_autonomous_trading": True,
        }
    )
    return summary


def _fixture_rows(fixture: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = fixture.get("mappings", fixture.get("url_mappings", []))
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _matching_fixture_row(
    rows: Sequence[Mapping[str, Any]],
    market_id: str,
    source_category: str,
    source_name: str,
) -> Mapping[str, Any] | None:
    for row in rows:
        if clean_text(row.get("market_id")) != market_id:
            continue
        if clean_text(row.get("source_category")) != source_category:
            continue
        row_name = clean_text(row.get("source_name")).lower()
        if row_name and row_name != source_name.lower():
            continue
        return row
    return None


def _local_concrete_public_urls(normalized_input: Mapping[str, Any]) -> list[str]:
    urls = []
    for packet in normalized_input.get("source_packets", []):
        if not isinstance(packet, Mapping):
            continue
        value = clean_text(packet.get("source_url_or_reference"))
        parsed = urlparse(value)
        if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
            urls.append(value)
    return urls


def _default_reason(url_status: str) -> str:
    if url_status == "concrete_safe_public_url":
        return "Concrete public URL was already present in local artifacts."
    if url_status == "blocked":
        return "Source category or fixture row is blocked by the local public-source registry."
    return "No concrete public HTTP(S) URL is present in local artifacts or the manual fixture."


def _optional_text(value: Any) -> str:
    if value is None:
        return ""
    return clean_text(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local-only source candidates for the PRACTICAL-017 new market.")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--fixture-json", default=None)
    parser.add_argument("--fixture-md", default=None)
    parser.add_argument("--normalized-input", default=str(DEFAULT_NORMALIZED_INPUT_PATH))
    args = parser.parse_args(argv)
    write_new_market_public_source_candidates(
        out_json_path=args.out_json,
        out_md_path=args.out_md,
        fixture_json_path=args.fixture_json,
        fixture_md_path=args.fixture_md,
        normalized_input_path=args.normalized_input,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
