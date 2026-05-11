from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.risk_engine import (
    APPROVED_OPERATOR_STATUSES,
    DECISION_ALLOWED,
    FRESH_EVIDENCE_STATUSES,
    SOURCE_GAP_FREE_STATUSES,
)
from pm_bot.trading_core.schemas import (
    ARTIFACT_DIR,
    GENERATED_AT,
    bullet_lines,
    clean_text,
    load_json_object,
    mapping_rows,
    trading_core_safety_summary,
    write_json,
    write_text,
)
from pm_bot.trading_core.wallet_execution_boundary import (
    EXECUTION_REQUEST_PACKET_CONTRACT,
    STATUS_APPROVED_FOR_FUTURE_SIMULATION,
    SAFETY_ASSERTION,
    validate_execution_request_packet,
)

DRY_RUN_EXECUTION_RECEIPT_CONTRACT = "pmbot_signing_simulator_dry_run_execution_receipt.v1"
DRY_RUN_EXECUTION_RECEIPT_LEDGER_CONTRACT = "pmbot_signing_simulator_dry_run_execution_receipt_ledger.v1"

MODE_DRY_RUN_ONLY = "dry_run_only"
MODE_SIMULATION_ONLY = "simulation_only"
STATUS_DRY_RUN_RECEIPT_READY = "dry_run_receipt_ready"
STATUS_BLOCKED = "blocked"

SIMULATOR_SAFETY_ASSERTION = "passive deterministic receipt only; no signing / no wallet / no order placement"


def simulate_signing_for_execution_request(
    packet: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    validation = validate_execution_request_packet(packet, generated_at=generated_at)
    action_packet = _action_packet(packet)
    gate_summary = _gate_summary(packet=packet, action_packet=action_packet, validation=validation)
    reason_codes = _receipt_reason_codes(validation=validation, gate_summary=gate_summary)
    status = STATUS_BLOCKED if reason_codes else STATUS_DRY_RUN_RECEIPT_READY
    packet_id = clean_text(packet.get("packet_id") or validation.get("packet_id"))
    receipt_id = _stable_id(
        "dry-run-execution-receipt-028",
        {
            "packet_id": packet_id,
            "action_packet_id": action_packet.get("action_packet_id"),
            "risk_decision_id": action_packet.get("risk_decision_id"),
            "status": status,
            "reason_codes": reason_codes,
            "mode": MODE_DRY_RUN_ONLY,
        },
    )
    simulated_artifact_id = _stable_id(
        "simulated-signing-artifact-028",
        {
            "packet_id": packet_id,
            "receipt_id": receipt_id,
            "mode": MODE_SIMULATION_ONLY,
        },
    )
    blocked_reason = reason_codes[0] if reason_codes else None
    return {
        "contract_version": DRY_RUN_EXECUTION_RECEIPT_CONTRACT,
        "receipt_id": receipt_id,
        "simulated_receipt_id": receipt_id,
        "request_id": packet_id,
        "packet_id": packet_id,
        "action_packet_id": clean_text(action_packet.get("action_packet_id")),
        "risk_decision_id": clean_text(action_packet.get("risk_decision_id")),
        "audit_id": clean_text(action_packet.get("audit_id")),
        "created_at": generated_at,
        "generated_at": generated_at,
        "mode": MODE_DRY_RUN_ONLY,
        "simulation_mode": MODE_SIMULATION_ONLY,
        "status": status,
        "blocked_reason": blocked_reason,
        "reason_codes": reason_codes,
        "gate_summary": gate_summary,
        "simulated_signing_result": {
            "status": "recorded_passive_simulation" if status == STATUS_DRY_RUN_RECEIPT_READY else "blocked",
            "simulated_artifact_id": simulated_artifact_id,
            "deterministic_receipt_id_only": True,
            "cryptographic_signing_performed": False,
            "wallet_material_accessed": False,
            "order_artifact_created": False,
            "authenticated_endpoint_prepared": False,
        },
        "paper_only": True,
        "live_prep_only": True,
        "simulation_only": True,
        "dry_run_only": True,
        "passive_artifact_only": True,
        "execution_enabled": False,
        "live_execution_enabled": False,
        "real_order_allowed": False,
        "real_order_submitted": False,
        "wallet_required": False,
        "wallet_used": False,
        "private_key_used": False,
        "signing_used": False,
        "real_signing_performed": False,
        "trading_endpoint_required": False,
        "trading_endpoint_used": False,
        "authenticated_endpoint_used": False,
        "external_api_calls_performed": False,
        "network_used": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def build_dry_run_execution_receipt_ledger(
    *,
    wallet_boundary_audit_ledger: Mapping[str, Any] | None = None,
    execution_request_packets: Sequence[Mapping[str, Any]] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    boundary_ledger = dict(wallet_boundary_audit_ledger or {})
    packets = list(execution_request_packets or mapping_rows(boundary_ledger.get("execution_request_packets")))
    receipts = [
        simulate_signing_for_execution_request(packet, generated_at=generated_at)
        for packet in packets
        if isinstance(packet, Mapping)
    ]
    reason_summary = _reason_code_summary(receipts)
    status_counts = _status_counts(receipts)
    receipt_ids = [clean_text(row.get("receipt_id")) for row in receipts]
    run_date = clean_text(boundary_ledger.get("run_date") or generated_at[:10])
    return {
        "contract_version": DRY_RUN_EXECUTION_RECEIPT_LEDGER_CONTRACT,
        "ledger_id": f"dry-run-execution-receipt-ledger-028-{run_date}",
        "generated_at": generated_at,
        "run_id": clean_text(boundary_ledger.get("run_id")),
        "run_date": run_date,
        "mode": MODE_DRY_RUN_ONLY,
        "simulation_mode": MODE_SIMULATION_ONLY,
        "receipt_count": len(receipts),
        "dry_run_receipt_ready_count": status_counts[STATUS_DRY_RUN_RECEIPT_READY],
        "blocked_receipt_count": status_counts[STATUS_BLOCKED],
        "request_packet_count": len(packets),
        "receipt_ids_unique": len(receipt_ids) == len(set(receipt_ids)),
        "reason_code_summary": reason_summary,
        "gate_enforcement_summary": _gate_enforcement_summary(receipts),
        "receipts": receipts,
        "idempotency": {
            "receipt_ids_unique": len(receipt_ids) == len(set(receipt_ids)),
            "deterministic_receipt_ids": True,
            "input_order_preserved": True,
            "unrelated_files_overwritten": False,
        },
        "safety_assertion": SIMULATOR_SAFETY_ASSERTION,
        "wallet_boundary_safety_assertion": clean_text(boundary_ledger.get("safety_assertion") or SAFETY_ASSERTION),
        "paper_only": True,
        "live_prep_only": True,
        "simulation_only": True,
        "dry_run_only": True,
        "passive_artifact_only": True,
        "applied_to_paper_execution": False,
        "applied_to_real_execution": False,
        "execution_enabled": False,
        "live_execution_enabled": False,
        "real_order_allowed": False,
        "real_order_submitted": False,
        "wallet_required": False,
        "wallet_used": False,
        "private_key_used": False,
        "signing_used": False,
        "real_signing_performed": False,
        "trading_endpoint_required": False,
        "trading_endpoint_used": False,
        "authenticated_endpoint_used": False,
        "external_api_calls_performed": False,
        "network_used": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
        "safety_summary": trading_core_safety_summary(),
    }


def write_dry_run_execution_receipt_ledger(
    *,
    wallet_boundary_audit_ledger: Mapping[str, Any] | None = None,
    execution_request_packets: Sequence[Mapping[str, Any]] | None = None,
    out_json_path: str | Path = ARTIFACT_DIR / "dry_run_execution_receipts.json",
    out_md_path: str | Path = ARTIFACT_DIR / "dry_run_execution_receipts.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    ledger = build_dry_run_execution_receipt_ledger(
        wallet_boundary_audit_ledger=wallet_boundary_audit_ledger,
        execution_request_packets=execution_request_packets,
        generated_at=generated_at,
    )
    write_json(out_json_path, ledger)
    write_text(out_md_path, render_dry_run_execution_receipt_ledger_markdown(ledger))
    return ledger


def load_and_write_dry_run_execution_receipt_ledger(
    *,
    wallet_boundary_audit_ledger_path: str | Path = ARTIFACT_DIR / "wallet_boundary_audit_ledger.json",
    out_json_path: str | Path = ARTIFACT_DIR / "dry_run_execution_receipts.json",
    out_md_path: str | Path = ARTIFACT_DIR / "dry_run_execution_receipts.md",
) -> dict[str, Any]:
    return write_dry_run_execution_receipt_ledger(
        wallet_boundary_audit_ledger=load_json_object(
            wallet_boundary_audit_ledger_path,
            label="wallet boundary audit ledger",
        ),
        out_json_path=out_json_path,
        out_md_path=out_md_path,
    )


def render_dry_run_execution_receipt_ledger_markdown(ledger: Mapping[str, Any]) -> str:
    gates = dict(ledger.get("gate_enforcement_summary", {}))
    lines = [
        "# PMBOT Dry-Run Execution Receipts",
        "",
        "- Passive signing simulator artifact; no wallet, private key, cryptographic signing, endpoint, or order placement is connected.",
        f"- Mode: `{ledger.get('mode')}` / `{ledger.get('simulation_mode')}`",
        f"- Receipts: {ledger.get('receipt_count')}",
        f"- Ready receipts: {ledger.get('dry_run_receipt_ready_count')}",
        f"- Blocked receipts: {ledger.get('blocked_receipt_count')}",
        f"- Receipt IDs unique: `{str(ledger.get('receipt_ids_unique')).lower()}`",
        f"- Boundary packet gate enforced: `{str(gates.get('valid_boundary_packet_required')).lower()}`",
        f"- Risk gate enforced: `{str(gates.get('risk_decision_required')).lower()}`",
        f"- Kill switch enforced: `{str(gates.get('kill_switch_must_be_disabled')).lower()}`",
        f"- Manual approval gate enforced: `{str(gates.get('manual_approval_gate_required')).lower()}`",
        f"- Evidence gate enforced: `{str(gates.get('evidence_gate_required')).lower()}`",
        f"- Forbidden fields rejected: `{str(gates.get('forbidden_fields_rejected')).lower()}`",
        "",
        "## Reason Code Summary",
        "",
        *bullet_lines(f"{key}: `{value}`" for key, value in dict(ledger.get("reason_code_summary", {})).items()),
        "",
        "## Receipts",
        "",
    ]
    for receipt in mapping_rows(ledger.get("receipts")):
        lines.extend(
            [
                f"- `{receipt.get('receipt_id')}` `{receipt.get('status')}` packet `{receipt.get('packet_id')}`",
                f"  - Risk decision: `{receipt.get('risk_decision_id')}`",
                f"  - Blocked reason: `{receipt.get('blocked_reason')}`",
                f"  - Reason codes: `{', '.join(receipt.get('reason_codes', []))}`",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _action_packet(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    action_packet = packet.get("risk_approved_action_packet")
    return action_packet if isinstance(action_packet, Mapping) else {}


def _gate_summary(
    *,
    packet: Mapping[str, Any],
    action_packet: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    snapshot = (
        dict(action_packet.get("risk_snapshot", {}))
        if isinstance(action_packet.get("risk_snapshot"), Mapping)
        else {}
    )
    manual_status = clean_text(action_packet.get("manual_approval_status")).lower()
    evidence_status = clean_text(action_packet.get("evidence_freshness_status")).lower()
    source_status = clean_text(action_packet.get("source_gap_status")).lower()
    forbidden_paths = list(validation.get("forbidden_field_paths", []))
    boundary_validation_status = clean_text(validation.get("status"))
    return {
        "packet_contract_valid": packet.get("contract_version") == EXECUTION_REQUEST_PACKET_CONTRACT,
        "boundary_validation_status": boundary_validation_status,
        "valid_boundary_packet": boundary_validation_status == STATUS_APPROVED_FOR_FUTURE_SIMULATION,
        "risk_decision_present": bool(clean_text(action_packet.get("risk_decision_id"))),
        "risk_audit_present": bool(clean_text(action_packet.get("audit_id"))),
        "risk_decision_allowed": clean_text(action_packet.get("risk_decision")) == DECISION_ALLOWED,
        "kill_switch_disabled": clean_text(action_packet.get("kill_switch_status")).lower() == "disabled",
        "manual_approval_gate_required": (
            action_packet.get("manual_approval_required") is True
            or snapshot.get("manual_approval_required") is True
        ),
        "manual_approval_present": manual_status in APPROVED_OPERATOR_STATUSES,
        "evidence_gate_required": snapshot.get("require_fresh_evidence") is True,
        "evidence_fresh": evidence_status in FRESH_EVIDENCE_STATUSES,
        "source_gap_gate_required": snapshot.get("block_on_source_gap") is True,
        "source_gap_free": source_status in SOURCE_GAP_FREE_STATUSES,
        "forbidden_field_paths_absent": not forbidden_paths,
        "forbidden_field_paths": [clean_text(item) for item in forbidden_paths],
        "dry_run_only": True,
        "simulation_only": True,
        "execution_enabled": False,
        "live_execution_enabled": False,
        "real_order_allowed": False,
        "real_order_submitted": False,
        "wallet_used": False,
        "private_key_used": False,
        "signing_used": False,
        "authenticated_endpoint_used": False,
    }


def _receipt_reason_codes(
    *,
    validation: Mapping[str, Any],
    gate_summary: Mapping[str, Any],
) -> list[str]:
    reasons = [clean_text(item) for item in validation.get("reason_codes", []) if clean_text(item)]
    checks = (
        ("valid_boundary_packet", "VALID_BOUNDARY_PACKET_REQUIRED"),
        ("risk_decision_present", "RISK_DECISION_REQUIRED"),
        ("risk_audit_present", "RISK_AUDIT_REQUIRED"),
        ("risk_decision_allowed", "RISK_DECISION_NOT_ALLOWED"),
        ("kill_switch_disabled", "KILL_SWITCH_MUST_BE_DISABLED"),
        ("manual_approval_gate_required", "MANUAL_APPROVAL_GATE_REQUIRED"),
        ("manual_approval_present", "MANUAL_APPROVAL_REQUIRED"),
        ("evidence_gate_required", "EVIDENCE_GATE_REQUIRED"),
        ("evidence_fresh", "EVIDENCE_NOT_FRESH"),
        ("source_gap_gate_required", "SOURCE_GAP_GATE_REQUIRED"),
        ("source_gap_free", "SOURCE_GAP_PRESENT"),
        ("forbidden_field_paths_absent", "FORBIDDEN_EXECUTION_REQUEST_FIELD_PRESENT"),
    )
    for key, reason in checks:
        if gate_summary.get(key) is not True:
            reasons.append(reason)
    return _dedupe(reasons)


def _gate_enforcement_summary(receipts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocked_for_forbidden = any(
        "FORBIDDEN_EXECUTION_REQUEST_FIELD_PRESENT" in receipt.get("reason_codes", [])
        for receipt in receipts
    )
    return {
        "valid_boundary_packet_required": True,
        "risk_decision_required": True,
        "kill_switch_must_be_disabled": True,
        "manual_approval_gate_required": True,
        "evidence_gate_required": True,
        "source_gap_gate_required": True,
        "forbidden_fields_rejected": blocked_for_forbidden
        or all(dict(receipt.get("gate_summary", {})).get("forbidden_field_paths_absent") is True for receipt in receipts),
        "all_receipts_passive": all(receipt.get("passive_artifact_only") is True for receipt in receipts),
    }


def _status_counts(receipts: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        STATUS_DRY_RUN_RECEIPT_READY: len(
            [receipt for receipt in receipts if receipt.get("status") == STATUS_DRY_RUN_RECEIPT_READY]
        ),
        STATUS_BLOCKED: len([receipt for receipt in receipts if receipt.get("status") == STATUS_BLOCKED]),
    }


def _reason_code_summary(receipts: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for receipt in receipts:
        for reason in receipt.get("reason_codes", []):
            reason_text = clean_text(reason)
            if reason_text:
                counts[reason_text] = counts.get(reason_text, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def _dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write PMBOT passive dry-run execution receipt artifacts.")
    parser.add_argument("--wallet-boundary-ledger", default=str(ARTIFACT_DIR / "wallet_boundary_audit_ledger.json"))
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "dry_run_execution_receipts.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "dry_run_execution_receipts.md"))
    args = parser.parse_args(argv)
    load_and_write_dry_run_execution_receipt_ledger(
        wallet_boundary_audit_ledger_path=args.wallet_boundary_ledger,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
