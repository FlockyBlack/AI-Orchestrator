from __future__ import annotations

import argparse
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, load_json_any, safe_summary, write_json, write_text
from pm_bot.practical.saved_public_evidence_packet import assert_valid_saved_public_evidence_packet

REPLAY_ADAPTER_CONTRACT_VERSION = "pmbot_saved_evidence_replay_adapter.v1"


def load_saved_evidence_packets(path: str) -> list[dict[str, Any]]:
    payload = load_json_any(path, label="saved evidence packet")
    if isinstance(payload, list):
        packets = payload
    elif isinstance(payload, dict) and isinstance(payload.get("evidence_packets"), list):
        packets = payload["evidence_packets"]
    elif isinstance(payload, dict):
        packets = [payload]
    else:
        raise ValueError("saved evidence input must be an object, list, or evidence_packets object")
    normalized: list[dict[str, Any]] = []
    for packet in packets:
        if not isinstance(packet, dict):
            raise ValueError("each saved evidence packet must be an object")
        assert_valid_saved_public_evidence_packet(packet)
        normalized.append(packet)
    return normalized


def map_saved_evidence_to_source_packets(packets: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    source_packets = [_source_packet_from_evidence(packet) for packet in packets]
    market_ids = sorted({market_id for packet in packets for market_id in packet.get("market_ids", [])})
    hypothesis_ids = sorted(
        {hypothesis_id for packet in packets for hypothesis_id in packet.get("hypothesis_ids", [])}
    )
    return {
        "contract_version": REPLAY_ADAPTER_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "replay_mode": True,
        "live_network_used": False,
        "market_ids": market_ids,
        "hypothesis_ids": hypothesis_ids,
        "source_packets": source_packets,
        "source_packet_format": "pmbot_one_market_input.v1 source_packets-compatible",
        "safety_notes": [
            "Saved evidence replay only.",
            "No network fetch is performed.",
            "Source IDs, source categories, freshness, limitations, and replay markers are preserved.",
        ],
        "safety_summary": safe_summary(),
    }


def write_saved_evidence_replay_adapter_sample(
    *,
    evidence_path: str,
    out_json_path: str | None = None,
    out_md_path: str | None = None,
) -> dict[str, Any]:
    packets = load_saved_evidence_packets(evidence_path)
    mapped = map_saved_evidence_to_source_packets(packets)
    if out_json_path is not None:
        write_json(out_json_path, mapped)
    if out_md_path is not None:
        write_text(out_md_path, render_saved_evidence_replay_adapter_markdown(mapped))
    return mapped


def render_saved_evidence_replay_adapter_markdown(mapped: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Saved Evidence Replay Adapter Sample",
        "",
        f"- Contract: `{mapped.get('contract_version')}`",
        f"- Replay mode: `{str(mapped.get('replay_mode')).lower()}`",
        f"- Live network used: `{str(mapped.get('live_network_used')).lower()}`",
        f"- Source packets: {len(mapped.get('source_packets', []))}",
        "",
        "## Markets",
        "",
        *bullet_lines(f"`{market_id}`" for market_id in mapped.get("market_ids", [])),
        "",
        "## Source Packets",
        "",
    ]
    for source in mapped.get("source_packets", []):
        lines.extend(
            [
                f"- `{source.get('source_id')}` {source.get('source_name')}",
                f"  Type: `{source.get('source_type')}`",
                f"  Category: `{source.get('source_category')}`",
                f"  Freshness: `{source.get('freshness_status')}`",
                f"  Replay: `{str(source.get('replay_mode')).lower()}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- Local saved evidence replay only.",
            "- No live fetch, authentication, wallet access, order path, or trading action is used.",
        ]
    )
    return "\n".join(lines) + "\n"


def _source_packet_from_evidence(packet: Mapping[str, Any]) -> dict[str, Any]:
    claims = packet.get("normalized_claims", [])
    limitations = list(packet.get("limitations", []))
    if packet.get("capture_errors"):
        limitations.extend(f"capture_error: {item}" for item in packet["capture_errors"])
    return {
        "source_id": packet.get("source_id", ""),
        "source_name": packet.get("source_name", ""),
        "source_type": "saved_public_evidence_replay",
        "source_category": packet.get("source_category", ""),
        "source_url_or_reference": packet.get("source_reference", ""),
        "captured_at": packet.get("captured_at", ""),
        "claim_type": "saved_public_evidence_claims",
        "claim_value": " | ".join(str(claim) for claim in claims),
        "evidence_summary": packet.get("raw_excerpt_or_summary", ""),
        "freshness_status": packet.get("freshness_status", ""),
        "known_limitations": limitations,
        "used_in_analysis": True,
        "replay_mode": True,
        "live_network_used": False,
        "evidence_packet_id": packet.get("evidence_packet_id", ""),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay local saved public evidence into source_packets-like JSON.")
    parser.add_argument("--evidence", required=True, help="Input saved evidence packet JSON.")
    parser.add_argument("--out-json", required=True, help="Output mapped source packets JSON.")
    parser.add_argument("--out-md", required=True, help="Output mapped source packets Markdown.")
    args = parser.parse_args(argv)
    write_saved_evidence_replay_adapter_sample(
        evidence_path=args.evidence,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
