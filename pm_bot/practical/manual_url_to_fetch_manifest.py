from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.manual_public_url_collection import (
    GENERATED_AT_017,
    NEW_MARKET_ID,
    NEW_MARKET_TITLE,
    manual_url_collection_safety_summary,
    validate_manual_public_url_collection_packet,
)
from pm_bot.practical.practical_io import bullet_lines, clean_text, load_json_object, slug_id, write_json, write_text

MANUAL_URL_TO_FETCH_MANIFEST_CONTRACT_VERSION = "pmbot_manual_url_to_fetch_manifest.v1"


def build_future_fetch_manifest_from_manual_packet(
    packet: Mapping[str, Any],
    *,
    max_request_count: int = 3,
    generated_at: str = GENERATED_AT_017,
) -> dict[str, Any]:
    candidate_count = len(_mapping_rows(packet.get("candidate_urls")))
    validation = validate_manual_public_url_collection_packet(
        packet,
        max_request_count=max(max_request_count, candidate_count),
        generated_at=generated_at,
    )
    candidate_results = _mapping_rows(validation.get("candidate_url_results"))
    packet_has_missing_urls = int(validation.get("missing_url_count") or 0) > 0

    executable: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    valid_seen = 0
    over_limit_seen = False

    for index, row in enumerate(candidate_results, start=1):
        status = clean_text(row.get("url_status"))
        if status == "missing":
            missing.append(_missing_intent(row, "missing operator-supplied URL"))
            continue
        if status == "blocked":
            blocked.append(_blocked_intent(row, "operator-supplied URL failed local safety validation"))
            continue
        if status != "valid_public_http_url":
            missing.append(_missing_intent(row, "URL has not reached valid_public_http_url status"))
            continue
        if packet_has_missing_urls:
            missing.append(_missing_intent(row, "packet still has missing URL rows; executable intents are held"))
            continue

        valid_seen += 1
        if valid_seen > max_request_count:
            over_limit_seen = True
            blocked.append(_blocked_intent(row, "valid URL exceeds max_request_count for the future manifest"))
            continue
        executable.append(_executable_intent(index, row, validation))

    within_request_limit = not over_limit_seen and len(executable) <= max_request_count
    ready_for_operator_approval = bool(executable) and not missing and not blocked and within_request_limit
    return {
        "contract_version": MANUAL_URL_TO_FETCH_MANIFEST_CONTRACT_VERSION,
        "generated_at": generated_at,
        "manifest_id": f"future-fetch-manifest-from-manual-packet-017b-{clean_text(packet.get('market_id') or NEW_MARKET_ID)}",
        "source_packet_id": clean_text(packet.get("packet_id")),
        "market_id": clean_text(packet.get("market_id") or NEW_MARKET_ID),
        "market_title": clean_text(packet.get("market_title") or NEW_MARKET_TITLE),
        "max_request_count": max_request_count,
        "executable_request_intents": executable,
        "missing_url_request_intents": missing,
        "blocked_request_intents": blocked,
        "executable_request_count": len(executable),
        "missing_url_count": len(missing),
        "blocked_request_count": len(blocked),
        "within_request_limit": within_request_limit,
        "ready_for_operator_approval": ready_for_operator_approval,
        "operator_approval_required_before_fetch": True,
        "operator_approval_granted": False,
        "live_fetch_performed": False,
        "no_real_trade_decision": True,
        "source_validation": validation,
        "safety_summary": manual_url_collection_safety_summary(),
    }


def render_future_fetch_manifest_from_manual_packet_markdown(manifest: Mapping[str, Any]) -> str:
    lines = [
        "# Future Fetch Manifest From Manual Packet 017B",
        "",
        f"- Source packet: `{manifest.get('source_packet_id')}`",
        f"- Market: `{manifest.get('market_id')}` {manifest.get('market_title')}",
        f"- Executable requests: {manifest.get('executable_request_count')}",
        f"- Missing URL requests: {manifest.get('missing_url_count')}",
        f"- Blocked requests: {manifest.get('blocked_request_count')}",
        f"- Within request limit: `{str(manifest.get('within_request_limit')).lower()}`",
        f"- Ready for operator approval: `{str(manifest.get('ready_for_operator_approval')).lower()}`",
        f"- Live fetch performed: `{str(manifest.get('live_fetch_performed')).lower()}`",
        "",
        "## Executable Request Intents",
        "",
    ]
    for row in _mapping_rows(manifest.get("executable_request_intents")):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}`",
                f"  Source: `{row.get('source_category')}` {row.get('source_name_or_placeholder')}",
                f"  URL: `{row.get('source_url')}`",
            ]
        )
    lines.extend(["", "## Missing URL Request Intents", ""])
    for row in _mapping_rows(manifest.get("missing_url_request_intents")):
        lines.extend(
            [
                f"- `{row.get('source_item_id')}`",
                f"  Source: `{row.get('source_category')}` {row.get('source_name_or_placeholder')}",
                f"  Reason: {row.get('non_executable_reason')}",
            ]
        )
    lines.extend(["", "## Blocked Request Intents", ""])
    for row in _mapping_rows(manifest.get("blocked_request_intents")):
        lines.extend(
            [
                f"- `{row.get('source_item_id')}`",
                f"  Source: `{row.get('source_category')}` {row.get('source_name_or_placeholder')}",
                f"  Reason: {row.get('blocked_reason')}",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- This manifest is a future request-intent preview only.",
            "- It does not fetch URLs and does not grant approval.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_future_fetch_manifest_from_manual_packet(
    *,
    packet_path: str | Path,
    out_json_path: str | Path,
    out_md_path: str | Path,
    max_request_count: int = 3,
) -> dict[str, Any]:
    packet = load_json_object(packet_path, label="manual URL collection packet")
    manifest = build_future_fetch_manifest_from_manual_packet(packet, max_request_count=max_request_count)
    write_json(out_json_path, manifest)
    write_text(out_md_path, render_future_fetch_manifest_from_manual_packet_markdown(manifest))
    return manifest


def _executable_intent(index: int, row: Mapping[str, Any], validation: Mapping[str, Any]) -> dict[str, Any]:
    source_name = clean_text(row.get("source_name"))
    item_id = clean_text(row.get("item_id"))
    market_id = clean_text(row.get("market_id") or validation.get("market_id") or NEW_MARKET_ID)
    source_url = clean_text(row.get("operator_supplied_url"))
    return {
        "request_intent_id": f"manual_url_fetch_request_017b_{index:02d}_{market_id}_{slug_id(source_name or item_id)}",
        "source_packet_id": clean_text(validation.get("source_packet_id")),
        "source_item_id": item_id,
        "market_id": market_id,
        "market_title": clean_text(validation.get("market_title") or NEW_MARKET_TITLE),
        "source_category": clean_text(row.get("source_category")),
        "source_name_or_placeholder": source_name,
        "source_reference": source_url,
        "source_url": source_url,
        "method": "GET",
        "expected_evidence_type": clean_text(row.get("expected_evidence_type")),
        "linked_hypothesis_id": clean_text(row.get("linked_hypothesis_id")),
        "url_status": "valid_public_http_url",
        "requires_auth": False,
        "credentials_required": False,
        "cookies_required": False,
        "trading_or_order_endpoint": False,
        "wallet_or_signing_required": False,
        "operator_approval_required_before_fetch": True,
        "live_fetch_performed": False,
        "url_safety_validation": row.get("url_safety_validation", {}),
    }


def _missing_intent(row: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "source_item_id": clean_text(row.get("item_id")),
        "market_id": clean_text(row.get("market_id") or NEW_MARKET_ID),
        "source_category": clean_text(row.get("source_category")),
        "source_name_or_placeholder": clean_text(row.get("source_name")),
        "expected_evidence_type": clean_text(row.get("expected_evidence_type")),
        "linked_hypothesis_id": clean_text(row.get("linked_hypothesis_id")),
        "url_status": clean_text(row.get("url_status") or "missing"),
        "non_executable_reason": reason,
        "live_fetch_performed": False,
    }


def _blocked_intent(row: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "source_item_id": clean_text(row.get("item_id")),
        "market_id": clean_text(row.get("market_id") or NEW_MARKET_ID),
        "source_category": clean_text(row.get("source_category")),
        "source_name_or_placeholder": clean_text(row.get("source_name")),
        "expected_evidence_type": clean_text(row.get("expected_evidence_type")),
        "linked_hypothesis_id": clean_text(row.get("linked_hypothesis_id")),
        "url_status": "blocked",
        "blocked_reason": reason,
        "safety_blockers": list(row.get("validation_notes", [])),
        "live_fetch_performed": False,
    }


def _mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a future fetch manifest from a manual URL packet.")
    parser.add_argument("--packet", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--max-request-count", type=int, default=3)
    args = parser.parse_args(argv)
    write_future_fetch_manifest_from_manual_packet(
        packet_path=args.packet,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
        max_request_count=args.max_request_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
