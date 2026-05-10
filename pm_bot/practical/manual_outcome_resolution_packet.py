from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.paper_update_approval import current_utc_timestamp
from pm_bot.practical.practical_io import bullet_lines, clean_text, safe_summary, write_json, write_text

MANUAL_OUTCOME_PACKET_CONTRACT_VERSION = "pmbot_manual_outcome_resolution_packet.v1"

OUTCOME_STATUSES = {"unresolved", "resolved", "void", "ambiguous"}
RESOLUTION_STATUSES = {"resolved", "void", "ambiguous"}
PAPER_HYPOTHESIS_RESULT_LABELS = {"pending", "aligned", "not_aligned", "ambiguous", "void"}

REQUIRED_PACKET_FIELDS = {
    "contract_version",
    "packet_id",
    "created_at",
    "market_id",
    "market_title",
    "hypothesis_id",
    "paper_tracking_snapshot_id",
    "outcome_status",
    "actual_outcome_summary",
    "resolved_at",
    "resolution_source_reference",
    "resolution_evidence_summary",
    "operator_notes",
    "source_evidence_used_for_resolution",
    "paper_hypothesis_result_label",
    "source_accuracy_lessons",
    "reasoning_lessons",
    "missing_evidence_lessons",
    "approval_required",
    "operator_approved",
    "no_real_trade_decision",
    "orders_or_trading_actions",
    "wallet_or_private_key_access",
}


class ManualOutcomeResolutionPacketError(ValueError):
    pass


def build_manual_outcome_resolution_packet(
    *,
    market_id: str,
    market_title: str,
    hypothesis_id: str,
    paper_tracking_snapshot_id: str,
    outcome_status: str = "unresolved",
    actual_outcome_summary: str = "",
    resolved_at: str = "",
    resolution_source_reference: str = "",
    resolution_evidence_summary: str = "",
    operator_notes: str = "",
    source_evidence_used_for_resolution: Sequence[Mapping[str, Any]] | None = None,
    paper_hypothesis_result_label: str = "pending",
    source_accuracy_lessons: Sequence[str] | None = None,
    reasoning_lessons: Sequence[str] | None = None,
    missing_evidence_lessons: Sequence[str] | None = None,
    operator_approved: bool = False,
    packet_id: str | None = None,
    created_at: str | None = None,
    synthetic_fixture: bool = False,
) -> dict[str, Any]:
    status = clean_text(outcome_status) or "unresolved"
    packet = {
        "contract_version": MANUAL_OUTCOME_PACKET_CONTRACT_VERSION,
        "packet_id": packet_id or f"manual-outcome-resolution-packet-014-{clean_text(market_id)}-{status}",
        "created_at": created_at or current_utc_timestamp(),
        "market_id": clean_text(market_id),
        "market_title": clean_text(market_title),
        "hypothesis_id": clean_text(hypothesis_id),
        "paper_tracking_snapshot_id": clean_text(paper_tracking_snapshot_id),
        "outcome_status": status,
        "actual_outcome_summary": clean_text(actual_outcome_summary),
        "resolved_at": clean_text(resolved_at),
        "resolution_source_reference": clean_text(resolution_source_reference),
        "resolution_evidence_summary": clean_text(resolution_evidence_summary),
        "operator_notes": clean_text(operator_notes),
        "source_evidence_used_for_resolution": [dict(row) for row in source_evidence_used_for_resolution or []],
        "paper_hypothesis_result_label": clean_text(paper_hypothesis_result_label) or "pending",
        "source_accuracy_lessons": _clean_list(source_accuracy_lessons),
        "reasoning_lessons": _clean_list(reasoning_lessons),
        "missing_evidence_lessons": _clean_list(missing_evidence_lessons),
        "approval_required": True,
        "operator_approved": bool(operator_approved),
        "no_real_trade_decision": True,
        "orders_or_trading_actions": False,
        "wallet_or_private_key_access": False,
        "safety_summary": _manual_outcome_packet_safety_summary(),
    }
    if synthetic_fixture:
        packet["synthetic_fixture"] = True
        packet["fixture_scope"] = "pm_bot/tests/fixtures/manual_outcome_feedback only"
    return packet


def validate_manual_outcome_resolution_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(field for field in REQUIRED_PACKET_FIELDS if field not in packet)
    errors.extend(f"missing required field: {field}" for field in missing)
    if errors:
        return errors

    if packet.get("contract_version") != MANUAL_OUTCOME_PACKET_CONTRACT_VERSION:
        errors.append("contract_version must be pmbot_manual_outcome_resolution_packet.v1")

    market_id = clean_text(packet.get("market_id"))
    if not market_id:
        errors.append("market_id is required")
    if not clean_text(packet.get("market_title")):
        errors.append("market_title is required")
    if not clean_text(packet.get("hypothesis_id")):
        errors.append("hypothesis_id is required")
    if not clean_text(packet.get("paper_tracking_snapshot_id")):
        errors.append("paper_tracking_snapshot_id is required")

    status = clean_text(packet.get("outcome_status"))
    label = clean_text(packet.get("paper_hypothesis_result_label"))
    if status not in OUTCOME_STATUSES:
        errors.append(f"outcome_status must be one of {sorted(OUTCOME_STATUSES)}")
    if label not in PAPER_HYPOTHESIS_RESULT_LABELS:
        errors.append(f"paper_hypothesis_result_label must be one of {sorted(PAPER_HYPOTHESIS_RESULT_LABELS)}")

    if packet.get("approval_required") is not True:
        errors.append("approval_required must be true")
    if packet.get("no_real_trade_decision") is not True:
        errors.append("no_real_trade_decision must be true")
    if packet.get("orders_or_trading_actions") is not False:
        errors.append("orders_or_trading_actions must be false")
    if packet.get("wallet_or_private_key_access") is not False:
        errors.append("wallet_or_private_key_access must be false")

    if not isinstance(packet.get("source_evidence_used_for_resolution"), list):
        errors.append("source_evidence_used_for_resolution must be a list")
    for list_field in ("source_accuracy_lessons", "reasoning_lessons", "missing_evidence_lessons"):
        if not isinstance(packet.get(list_field), list):
            errors.append(f"{list_field} must be a list")

    if status == "unresolved":
        errors.extend(_validate_unresolved_packet(packet, label))
    elif status in RESOLUTION_STATUSES:
        errors.extend(_validate_resolution_packet(packet, status, label))

    return errors


def assert_valid_manual_outcome_resolution_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_manual_outcome_resolution_packet(packet)
    if errors:
        raise ManualOutcomeResolutionPacketError("; ".join(errors))


def packet_claims_real_outcome(packet: Mapping[str, Any]) -> bool:
    status = clean_text(packet.get("outcome_status"))
    if status in RESOLUTION_STATUSES:
        return True
    return any(
        bool(clean_text(packet.get(field)))
        for field in ("actual_outcome_summary", "resolved_at", "resolution_source_reference", "resolution_evidence_summary")
    )


def render_manual_outcome_resolution_packet_markdown(packet: Mapping[str, Any]) -> str:
    status = clean_text(packet.get("outcome_status"))
    lines = [
        "# Manual Outcome Resolution Packet",
        "",
        f"- Packet ID: `{packet.get('packet_id')}`",
        f"- Market: `{packet.get('market_id')}` - {packet.get('market_title')}",
        f"- Hypothesis: `{packet.get('hypothesis_id')}`",
        f"- Outcome status: `{status}`",
        f"- Paper result label: `{packet.get('paper_hypothesis_result_label')}`",
        f"- Operator approved: `{str(packet.get('operator_approved')).lower()}`",
        "",
    ]
    if status == "unresolved":
        lines.extend(
            [
                "## Resolution Status",
                "",
                "- No resolved outcome is claimed in this packet.",
                "- The operator must add a local resolution source later before feedback can be ready.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Resolution Status",
                "",
                f"- Actual outcome summary: {packet.get('actual_outcome_summary')}",
                f"- Resolved at: `{packet.get('resolved_at')}`",
                f"- Resolution source reference: {packet.get('resolution_source_reference')}",
                f"- Resolution evidence summary: {packet.get('resolution_evidence_summary')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Lessons",
            "",
            "### Source Accuracy",
            "",
            *bullet_lines(str(item) for item in packet.get("source_accuracy_lessons", [])),
            "",
            "### Reasoning",
            "",
            *bullet_lines(str(item) for item in packet.get("reasoning_lessons", [])),
            "",
            "### Missing Evidence",
            "",
            *bullet_lines(str(item) for item in packet.get("missing_evidence_lessons", [])),
            "",
            "## Safety",
            "",
            "- approval_required: `true`",
            "- no_real_trade_decision: `true`",
            "- orders_or_trading_actions: `false`",
            "- wallet_or_private_key_access: `false`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_manual_outcome_resolution_packet(
    packet: Mapping[str, Any],
    *,
    out_json_path: str | Path,
    out_md_path: str | Path,
) -> None:
    assert_valid_manual_outcome_resolution_packet(packet)
    write_json(out_json_path, dict(packet))
    write_text(out_md_path, render_manual_outcome_resolution_packet_markdown(packet))


def _validate_unresolved_packet(packet: Mapping[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    if label != "pending":
        errors.append("unresolved packets must use paper_hypothesis_result_label pending")
    if packet.get("operator_approved") is not False:
        errors.append("unresolved packets must not be operator_approved")
    for field in ("actual_outcome_summary", "resolved_at", "resolution_source_reference", "resolution_evidence_summary"):
        if clean_text(packet.get(field)):
            errors.append(f"unresolved packets must leave {field} empty")
    if packet.get("source_evidence_used_for_resolution"):
        errors.append("unresolved packets must not include source_evidence_used_for_resolution")
    return errors


def _validate_resolution_packet(packet: Mapping[str, Any], status: str, label: str) -> list[str]:
    errors: list[str] = []
    for field in ("actual_outcome_summary", "resolved_at", "resolution_source_reference", "resolution_evidence_summary"):
        if not clean_text(packet.get(field)):
            errors.append(f"{status} packets require {field}")
    if packet.get("operator_approved") is not True:
        errors.append(f"{status} packets require operator approval")
    if status == "resolved" and label not in {"aligned", "not_aligned", "ambiguous"}:
        errors.append("resolved packets must use aligned, not_aligned, or ambiguous result labels")
    if status == "ambiguous" and label != "ambiguous":
        errors.append("ambiguous packets must use paper_hypothesis_result_label ambiguous")
    if status == "void" and label != "void":
        errors.append("void packets must use paper_hypothesis_result_label void")
    return errors


def _clean_list(values: Sequence[str] | None) -> list[str]:
    return [clean_text(value) for value in values or [] if clean_text(value)]


def _manual_outcome_packet_safety_summary() -> dict[str, Any]:
    summary = safe_summary()
    summary.update(
        {
            "new_live_fetch_performed": False,
            "openrouter_calls_performed": 0,
            "new_polymarket_api_calls_performed": 0,
            "authenticated_endpoints_used": False,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "runtime_or_dispatcher_changes": False,
            "market_recommendation_generated": False,
            "probability_ev_edge_or_side_selection_generated": False,
            "outcome_resolution_invented": False,
            "no_scheduler_daemon_background_worker": True,
            "no_autonomous_trading": True,
        }
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a PMBOT manual outcome resolution packet.")
    parser.add_argument("packet", help="Local manual outcome packet JSON path.")
    args = parser.parse_args(argv)
    import json

    packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    assert_valid_manual_outcome_resolution_packet(packet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
