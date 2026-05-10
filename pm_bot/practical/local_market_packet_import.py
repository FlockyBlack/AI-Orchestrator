from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.one_market_analysis import INPUT_CONTRACT_VERSION, validate_one_market_input
from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_string_list, clean_text, load_json_object, write_json, write_text

IMPORT_CONTRACT_VERSION = "pmbot_local_market_packet_import.v1"


class LocalMarketPacketImportError(ValueError):
    pass


def normalize_local_market_packet(path: str | Path) -> dict[str, Any]:
    payload = load_json_object(path, label="local market packet")
    if payload.get("contract_version") == INPUT_CONTRACT_VERSION:
        validation = validate_one_market_input(payload)
        if not validation.valid:
            raise LocalMarketPacketImportError("; ".join(validation.errors))
        return dict(payload)

    market = payload.get("market") if isinstance(payload.get("market"), Mapping) else payload
    sources = payload.get("source_packets", payload.get("sources", payload.get("source_packets_local", [])))
    if not isinstance(sources, list):
        raise LocalMarketPacketImportError("packet sources must be a list")
    if not sources:
        raise LocalMarketPacketImportError("packet must include at least one local source reference")

    missing_evidence = clean_string_list(payload.get("missing_evidence"))
    normalized_sources = [_normalize_source(source, index=index, missing_evidence=missing_evidence) for index, source in enumerate(sources)]
    normalized = {
        "available_evidence": clean_string_list(payload.get("available_evidence"))
        or [source["evidence_summary"] for source in normalized_sources if source["used_in_analysis"]],
        "contract_version": INPUT_CONTRACT_VERSION,
        "created_at": clean_text(payload.get("created_at") or GENERATED_AT),
        "current_context_summary": clean_text(
            payload.get("current_context_summary")
            or payload.get("context")
            or market.get("context")
            or "Local packet did not include a detailed context summary."
        ),
        "known_uncertainties": clean_string_list(payload.get("known_uncertainties"))
        or ["Local packet may be incomplete; missing evidence is preserved below."],
        "market_id": clean_text(payload.get("market_id") or market.get("market_id") or market.get("id")),
        "market_slug_or_reference": clean_text(
            payload.get("market_slug_or_reference")
            or payload.get("market_reference")
            or market.get("slug")
            or market.get("reference")
            or market.get("market_id")
            or market.get("id")
        ),
        "market_title": clean_text(payload.get("market_title") or payload.get("title") or market.get("title")),
        "market_type": clean_text(payload.get("market_type") or market.get("market_type") or "binary_resolution"),
        "missing_evidence": missing_evidence or ["No final outcome evidence was provided in the local packet."],
        "operator_notes": clean_string_list(payload.get("operator_notes"))
        or ["Normalized from a local packet without live fetching."],
        "outcomes": clean_string_list(payload.get("outcomes") or market.get("outcomes")) or ["yes", "no"],
        "resolution_source_summary": clean_text(
            payload.get("resolution_source_summary")
            or payload.get("resolution")
            or market.get("resolution_source_summary")
            or "Resolution source was not fully specified in the local packet."
        ),
        "rules_summary": clean_text(payload.get("rules_summary") or payload.get("rules") or market.get("rules")),
        "source_packets": normalized_sources,
    }
    required = ["market_id", "market_title", "rules_summary"]
    missing_required = [field for field in required if not normalized[field]]
    if missing_required:
        raise LocalMarketPacketImportError("packet missing required fields: " + ", ".join(missing_required))
    validation = validate_one_market_input(normalized)
    if not validation.valid:
        raise LocalMarketPacketImportError("; ".join(validation.errors))
    return normalized


def run_local_market_packet_import(
    *,
    input_path: str | Path,
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    normalized = normalize_local_market_packet(input_path)
    if out_json_path is not None:
        write_json(out_json_path, normalized)
    if out_md_path is not None:
        write_text(out_md_path, render_import_summary(normalized, input_path=input_path, out_json_path=out_json_path))
    return normalized


def render_import_summary(
    normalized: Mapping[str, Any],
    *,
    input_path: str | Path,
    out_json_path: str | Path | None = None,
) -> str:
    lines = [
        "# PMBOT Local Market Packet Import",
        "",
        f"- Input: `{input_path}`",
        f"- Output contract: `{normalized['contract_version']}`",
        f"- Market ID: `{normalized['market_id']}`",
        f"- Market title: {normalized['market_title']}",
        f"- Sources preserved: {len(normalized['source_packets'])}",
        f"- Missing evidence items: {len(normalized['missing_evidence'])}",
    ]
    if out_json_path is not None:
        lines.append(f"- Normalized JSON: `{out_json_path}`")
    lines.extend(
        [
            "",
            "## Missing evidence",
            "",
            *bullet_lines(normalized["missing_evidence"]),
            "",
            "## Source references",
            "",
            *bullet_lines(
                f"`{source['source_id']}` {source['source_name']} - `{source['freshness_status']}`"
                for source in normalized["source_packets"]
            ),
            "",
            "## Safety boundary",
            "",
            "- Local packet normalization only.",
            "- No live fetch or external API call was performed.",
            "- Missing evidence is preserved instead of invented.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize a local market packet into PMBOT one-market input JSON.")
    parser.add_argument("--input", required=True, help="Local raw packet, seed, or one-market input JSON.")
    parser.add_argument("--out-json", required=True, help="Output normalized one-market input JSON.")
    parser.add_argument("--out-md", required=True, help="Output import summary Markdown.")
    args = parser.parse_args(argv)

    run_local_market_packet_import(input_path=args.input, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


def _normalize_source(source: Any, *, index: int, missing_evidence: list[str]) -> dict[str, Any]:
    if not isinstance(source, Mapping):
        raise LocalMarketPacketImportError(f"source {index} must be an object")
    source_id = clean_text(source.get("source_id") or source.get("id") or f"local_source_{index + 1}")
    source_name = clean_text(source.get("source_name") or source.get("name") or source_id)
    evidence_summary = clean_text(source.get("evidence_summary") or source.get("summary"))
    if not evidence_summary:
        evidence_summary = f"Missing evidence summary in local packet for {source_name}."
        missing_evidence.append(evidence_summary)
    claim_type = clean_text(source.get("claim_type") or "local_packet_claim")
    claim_value = clean_text(source.get("claim_value") or source.get("claim") or "not_specified_in_local_packet")
    reference = clean_text(source.get("source_url_or_reference") or source.get("reference") or source.get("path"))
    if not reference:
        reference = f"local_packet_source_reference_missing:{source_id}"
        missing_evidence.append(f"Source reference missing for {source_name}.")
    return {
        "captured_at": clean_text(source.get("captured_at") or GENERATED_AT),
        "claim_type": claim_type,
        "claim_value": claim_value,
        "evidence_summary": evidence_summary,
        "freshness_status": clean_text(source.get("freshness_status") or source.get("freshness") or "unknown"),
        "known_limitations": clean_string_list(source.get("known_limitations"))
        or ["Limitations were not fully specified in the local packet."],
        "source_id": source_id,
        "source_name": source_name,
        "source_type": clean_text(source.get("source_type") or source.get("type") or "local_static_fixture"),
        "source_url_or_reference": reference,
        "used_in_analysis": source.get("used_in_analysis", True) is True,
    }


if __name__ == "__main__":
    raise SystemExit(main())
