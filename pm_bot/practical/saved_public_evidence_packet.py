from __future__ import annotations

import argparse
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_string_list, clean_text, load_json_object, safe_summary, write_json, write_text
from pm_bot.practical.public_source_registry import validate_source_category

SAVED_EVIDENCE_PACKET_CONTRACT_VERSION = "pmbot_saved_public_evidence_packet.v1"
CAPTURE_MODES = {"fixture", "replay", "future_public_read_only_fetch"}
REQUIRED_EVIDENCE_FIELDS = (
    "contract_version",
    "evidence_packet_id",
    "captured_at",
    "capture_mode",
    "live_network_used",
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
)


class SavedPublicEvidencePacketError(ValueError):
    pass


def build_saved_public_evidence_packet(
    *,
    evidence_packet_id: str,
    source_id: str,
    source_name: str,
    source_category: str,
    source_reference: str,
    market_ids: Sequence[str],
    hypothesis_ids: Sequence[str],
    raw_excerpt_or_summary: str,
    normalized_claims: Sequence[str],
    freshness_status: str = "fresh",
    contradiction_candidates: Sequence[str] = (),
    limitations: Sequence[str] = (),
    capture_mode: str = "fixture",
) -> dict[str, Any]:
    packet = {
        "contract_version": SAVED_EVIDENCE_PACKET_CONTRACT_VERSION,
        "evidence_packet_id": clean_text(evidence_packet_id),
        "captured_at": GENERATED_AT,
        "capture_mode": clean_text(capture_mode),
        "live_network_used": False,
        "source_id": clean_text(source_id),
        "source_name": clean_text(source_name),
        "source_category": clean_text(source_category),
        "source_reference": clean_text(source_reference),
        "market_ids": [clean_text(market_id) for market_id in market_ids],
        "hypothesis_ids": [clean_text(hypothesis_id) for hypothesis_id in hypothesis_ids],
        "raw_excerpt_or_summary": clean_text(raw_excerpt_or_summary),
        "normalized_claims": [clean_text(claim) for claim in normalized_claims],
        "freshness_status": clean_text(freshness_status),
        "contradiction_candidates": [clean_text(candidate) for candidate in contradiction_candidates],
        "limitations": list(limitations)
        or [
            "Fixture evidence only.",
            "Not captured from a live public source in this task.",
        ],
        "capture_errors": [],
        "auth_used": False,
        "credentials_used": False,
        "wallet_or_private_key_access": False,
        "orders_or_trading_actions": False,
        "safe_for_replay": True,
        "safety_summary": safe_summary(),
    }
    validation = validate_saved_public_evidence_packet(packet)
    if not validation["valid"]:
        raise SavedPublicEvidencePacketError("; ".join(validation["errors"]))
    return packet


def validate_saved_public_evidence_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = [field for field in REQUIRED_EVIDENCE_FIELDS if field not in packet]
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
        return {"valid": False, "errors": errors, "warnings": warnings}
    if packet.get("contract_version") != SAVED_EVIDENCE_PACKET_CONTRACT_VERSION:
        errors.append("contract_version must be " + SAVED_EVIDENCE_PACKET_CONTRACT_VERSION)
    for field in ("evidence_packet_id", "captured_at", "source_id", "source_name", "source_category", "source_reference"):
        if not clean_text(packet.get(field)):
            errors.append(f"{field} is required")
    if packet.get("capture_mode") not in CAPTURE_MODES:
        errors.append("capture_mode is not allowed")
    if packet.get("live_network_used") is not False:
        errors.append("live_network_used must be false for local fixtures and replay")
    if packet.get("auth_used") is not False:
        errors.append("auth_used must be false")
    if packet.get("credentials_used") is not False:
        errors.append("credentials_used must be false")
    if packet.get("wallet_or_private_key_access") is not False:
        errors.append("wallet_or_private_key_access must be false")
    if packet.get("orders_or_trading_actions") is not False:
        errors.append("orders_or_trading_actions must be false")
    if packet.get("safe_for_replay") is not True:
        errors.append("safe_for_replay must be true")
    if not isinstance(packet.get("market_ids"), list) or not packet["market_ids"]:
        errors.append("market_ids must be a non-empty list")
    if not isinstance(packet.get("hypothesis_ids"), list):
        errors.append("hypothesis_ids must be a list")
    if not isinstance(packet.get("normalized_claims"), list) or not packet["normalized_claims"]:
        errors.append("normalized_claims must be a non-empty list")
    if not isinstance(packet.get("contradiction_candidates"), list):
        errors.append("contradiction_candidates must be a list")
    if not isinstance(packet.get("limitations"), list):
        errors.append("limitations must be a list")
    if not isinstance(packet.get("capture_errors"), list):
        errors.append("capture_errors must be a list")
    category_validation = validate_source_category(clean_text(packet.get("source_category")))
    if category_validation["blocked"]:
        errors.append(f"source_category is blocked: {category_validation['source_category']}")
    if packet.get("freshness_status") == "stale":
        warnings.append("evidence is marked stale")
    if packet.get("contradiction_candidates"):
        warnings.append("evidence includes contradiction candidates")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def assert_valid_saved_public_evidence_packet(packet: Mapping[str, Any]) -> None:
    validation = validate_saved_public_evidence_packet(packet)
    if not validation["valid"]:
        raise SavedPublicEvidencePacketError("; ".join(validation["errors"]))


def render_saved_public_evidence_packet_markdown(packet: Mapping[str, Any]) -> str:
    validation = validate_saved_public_evidence_packet(packet)
    lines = [
        "# PMBOT Saved Public Evidence Packet",
        "",
        f"- Contract: `{packet.get('contract_version')}`",
        f"- Evidence packet ID: `{packet.get('evidence_packet_id')}`",
        f"- Capture mode: `{packet.get('capture_mode')}`",
        f"- Live network used: `{str(packet.get('live_network_used')).lower()}`",
        f"- Source: `{packet.get('source_id')}` {packet.get('source_name')}",
        f"- Source category: `{packet.get('source_category')}`",
        f"- Freshness: `{packet.get('freshness_status')}`",
        f"- Safe for replay: `{str(packet.get('safe_for_replay')).lower()}`",
        "",
        "## Markets",
        "",
        *bullet_lines(f"`{market_id}`" for market_id in packet.get("market_ids", [])),
        "",
        "## Normalized Claims",
        "",
        *bullet_lines(packet.get("normalized_claims", [])),
        "",
        "## Summary",
        "",
        packet.get("raw_excerpt_or_summary", ""),
        "",
        "## Contradiction Candidates",
        "",
        *bullet_lines(packet.get("contradiction_candidates", [])),
        "",
        "## Limitations",
        "",
        *bullet_lines(packet.get("limitations", [])),
        "",
        "## Validation",
        "",
        *bullet_lines(validation["errors"] + validation["warnings"]),
        "",
        "## Safety Boundary",
        "",
        "- Local saved evidence format only.",
        "- No authenticated source, wallet access, order path, trading action, or live network fetch is used.",
    ]
    return "\n".join(lines) + "\n"


def write_saved_public_evidence_packet(
    packet: Mapping[str, Any],
    *,
    out_json_path: str | None = None,
    out_md_path: str | None = None,
) -> dict[str, Any]:
    packet_dict = dict(packet)
    assert_valid_saved_public_evidence_packet(packet_dict)
    if out_json_path is not None:
        write_json(out_json_path, packet_dict)
    if out_md_path is not None:
        write_text(out_md_path, render_saved_public_evidence_packet_markdown(packet_dict))
    return packet_dict


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and render a local saved public evidence packet.")
    parser.add_argument("--evidence", required=True, help="Input saved evidence packet JSON.")
    parser.add_argument("--out-json", required=True, help="Output evidence packet JSON.")
    parser.add_argument("--out-md", required=True, help="Output evidence packet Markdown.")
    args = parser.parse_args(argv)
    packet = load_json_object(args.evidence, label="saved evidence packet")
    write_saved_public_evidence_packet(packet, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
