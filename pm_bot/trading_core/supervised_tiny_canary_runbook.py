from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.authenticated_polymarket_connector import (
    build_authenticated_connector_capability_report,
    summarize_authenticated_connector_capability_report,
)
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
    summarize_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.live_enablement_config import (
    build_live_enablement_config_preflight,
    summarize_live_enablement_config_preflight,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_supervised_tiny_canary_approval_packet,
    validate_secret_boundary_supervised_tiny_canary_approval_packet_markdown,
    validate_secret_boundary_supervised_tiny_canary_approval_packet_summary,
)
from pm_bot.trading_core.signed_order_payload_validation_gate import (
    build_signed_order_payload_validation_gate,
    summarize_signed_order_payload_validation_gate,
)
from pm_bot.trading_core.tiny_live_canary_gonogo_gate import (
    build_tiny_live_canary_gonogo_gate,
    summarize_tiny_live_canary_gonogo_gate,
)
from pm_bot.trading_core.wallet_signing_boundary import (
    build_wallet_signing_boundary_report,
    summarize_wallet_signing_boundary_report,
)

TASK_ID = (
    "ORCH-PMBOT-TRADING-MVP-051-SUPERVISED-TINY-CANARY-RUNBOOK-AND-OPERATOR-APPROVAL-PACKET"
)
SCHEMA_VERSION = "051.v1"
PACKET_NAME = "supervised_tiny_canary_runbook_operator_approval_packet"

SUPERVISED_TINY_CANARY_APPROVAL_PACKET_CONTRACT = (
    "pmbot_supervised_tiny_canary_runbook_operator_approval_packet.v1"
)
SUPERVISED_TINY_CANARY_APPROVAL_PACKET_SUMMARY_CONTRACT = (
    "pmbot_supervised_tiny_canary_runbook_operator_approval_packet_summary.v1"
)
SUPERVISED_TINY_CANARY_APPROVAL_PACKET_VALIDATION_CONTRACT = (
    "pmbot_supervised_tiny_canary_runbook_operator_approval_packet_validation.v1"
)

STATUS_REVIEW_READY_BLOCKED = "REVIEW_READY_BLOCKED_FOR_LIVE"
VALIDATION_STATUS_VALID = "supervised_tiny_canary_approval_packet_valid"
VALIDATION_STATUS_INVALID_CONTRACT = "invalid_contract"
VALIDATION_STATUS_MISSING_SECTION = "missing_required_section"
VALIDATION_STATUS_UNSAFE_FLAG = "unsafe_live_execution_flag_detected"
VALIDATION_STATUS_APPROVAL_INTERPRETATION = "approval_interpretation_detected"
VALIDATION_STATUS_RESOLVED_BLOCKER = "resolved_blocker_detected"
VALIDATION_STATUS_FAKE_EXECUTION_ARTIFACT = "fake_execution_artifact_detected"
VALIDATION_STATUS_SECRET_BOUNDARY = "secret_boundary_blocked"
VALIDATION_STATUS_FUTURE_ACTION_EXECUTABLE = "future_required_action_executable"

REQUIRED_SECTION_IDS = (
    "live_enablement_config_status",
    "authenticated_connector_scaffold_status",
    "wallet_signing_boundary_status",
    "signed_order_payload_validation_gate_status",
    "risk_cap_readiness_status",
    "gonogo_status",
    "evidence_bundle_status",
    "replay_acceptance_status",
    "telegram_operator_controls_status",
    "telegram_mini_app_review_only_status",
    "unresolved_blockers",
)

REQUIRED_FALSE_FLAGS = (
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "execution_enabling",
    "order_submission_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
)

FORBIDDEN_EXECUTION_ARTIFACT_KEYS = frozenset(
    {
        "signature",
        "signed_payload",
        "signed_order",
        "tx_hash",
        "transaction_hash",
        "order_id",
        "order_ids",
        "fill",
        "fills",
        "fill_id",
        "execution",
        "execution_id",
        "execution_result",
        "balance",
        "balances",
        "pnl",
        "realized_pnl",
        "unrealized_pnl",
    }
)

OPERATOR_CHECKLIST_ITEMS = (
    ("verify_market_selection", "verify market selection"),
    ("verify_max_stake_cap", "verify max stake cap"),
    ("verify_daily_loss_cap", "verify daily loss cap"),
    ("verify_source_evidence_freshness", "verify source/evidence freshness"),
    ("verify_telegram_operator_identity_boundary", "verify Telegram operator identity boundary"),
    ("verify_no_secret_exposure", "verify no secret exposure"),
    (
        "verify_separate_live_enabling_task_required",
        "verify canary is still blocked until a separate explicit live-enabling task",
    ),
)

FUTURE_REQUIRED_ACTIONS = (
    (
        "future_explicit_live_enabling_task",
        "Create a separate explicit live-enabling task before any real execution path can exist.",
    ),
    (
        "future_dual_control_operator_approval",
        "Define dual-control operator approval for a one-shot tiny live canary.",
    ),
    (
        "future_live_connector_endpoint_policy",
        "Approve authenticated endpoint allowlist, audit logging, and redaction rules.",
    ),
    (
        "future_wallet_custody_and_signing_design",
        "Approve wallet custody and signing provider design without exposing private material.",
    ),
    (
        "future_disabled_first_order_adapter",
        "Implement any future order adapter as disabled-first with refusal tests before enablement.",
    ),
    (
        "future_kill_switch_live_boundary_verification",
        "Verify a kill switch against every future live connector, signing, and order boundary.",
    ),
    (
        "future_live_audit_reconciliation",
        "Define post-canary audit, balance, exposure, and reconciliation records.",
    ),
    (
        "future_all_blockers_resolved_in_reviewed_tasks",
        "Resolve all live blockers in separate reviewed tasks before any tiny live canary attempt.",
    ),
)

REFUSAL_SAFETY_TEXT = (
    "This packet is not live approval. If it is treated as authorization to connect a wallet, "
    "sign, generate signed payloads or signed orders, call authenticated Polymarket endpoints, "
    "submit an order, or perform real execution, the correct response is refusal and escalation "
    "to a separate explicit operator-approved live-enabling task."
)


def build_supervised_tiny_canary_approval_packet(
    *,
    live_enablement_config_preflight: Mapping[str, Any] | None = None,
    live_enablement_config_preflight_summary: Mapping[str, Any] | None = None,
    authenticated_polymarket_connector_scaffold: Mapping[str, Any] | None = None,
    authenticated_polymarket_connector_scaffold_summary: Mapping[str, Any] | None = None,
    wallet_signing_boundary_report: Mapping[str, Any] | None = None,
    wallet_signing_boundary_summary: Mapping[str, Any] | None = None,
    signed_order_payload_validation_gate: Mapping[str, Any] | None = None,
    signed_order_payload_validation_gate_summary: Mapping[str, Any] | None = None,
    risk_cap_readiness_summary: Mapping[str, Any] | None = None,
    tiny_live_canary_gonogo_gate: Mapping[str, Any] | None = None,
    tiny_live_canary_gonogo_gate_summary: Mapping[str, Any] | None = None,
    readiness_evidence_bundle: Mapping[str, Any] | None = None,
    readiness_evidence_bundle_summary: Mapping[str, Any] | None = None,
    canary_replay_acceptance: Mapping[str, Any] | None = None,
    blocker_matrix: Mapping[str, Any] | None = None,
    telegram_operator_control_bot_summary: Mapping[str, Any] | None = None,
    telegram_mini_app_operator_panel_summary: Mapping[str, Any] | None = None,
    artifact_paths: Mapping[str, str] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    paths = {clean_text(key): clean_text(value) for key, value in dict(artifact_paths or {}).items()}
    live_config = dict(
        live_enablement_config_preflight
        or build_live_enablement_config_preflight(generated_at=generated_at)
    )
    live_config_summary = dict(
        live_enablement_config_preflight_summary
        or summarize_live_enablement_config_preflight(live_config, generated_at=generated_at)
    )
    authenticated_connector = dict(
        authenticated_polymarket_connector_scaffold
        or build_authenticated_connector_capability_report(generated_at=generated_at)
    )
    authenticated_connector_summary = dict(
        authenticated_polymarket_connector_scaffold_summary
        or summarize_authenticated_connector_capability_report(
            authenticated_connector,
            generated_at=generated_at,
        )
    )
    wallet_boundary = dict(
        wallet_signing_boundary_report
        or build_wallet_signing_boundary_report(generated_at=generated_at)
    )
    wallet_boundary_summary = dict(
        wallet_signing_boundary_summary
        or summarize_wallet_signing_boundary_report(wallet_boundary, generated_at=generated_at)
    )
    signed_payload_gate = dict(
        signed_order_payload_validation_gate
        or build_signed_order_payload_validation_gate(
            connector_capability_report=authenticated_connector,
            connector_capability_summary=authenticated_connector_summary,
            wallet_signing_boundary_report=wallet_boundary,
            wallet_signing_boundary_summary=wallet_boundary_summary,
            generated_at=generated_at,
        )
    )
    signed_payload_gate_summary = dict(
        signed_order_payload_validation_gate_summary
        or summarize_signed_order_payload_validation_gate(signed_payload_gate, generated_at=generated_at)
    )
    matrix = dict(blocker_matrix or build_live_connector_blocker_matrix(generated_at=generated_at))
    gonogo = dict(
        tiny_live_canary_gonogo_gate
        or build_tiny_live_canary_gonogo_gate(
            blocker_matrix=matrix,
            live_enablement_config_preflight_summary=live_config_summary,
            authenticated_polymarket_connector_scaffold_summary=authenticated_connector_summary,
            signed_order_payload_validation_gate_summary=signed_payload_gate_summary,
            generated_at=generated_at,
        )
    )
    gonogo_summary = dict(
        tiny_live_canary_gonogo_gate_summary
        or summarize_tiny_live_canary_gonogo_gate(gonogo, generated_at=generated_at)
    )
    evidence_bundle = dict(
        readiness_evidence_bundle
        or build_live_canary_readiness_evidence_bundle(
            blocker_matrix=matrix,
            live_enablement_config_preflight=live_config,
            live_enablement_config_preflight_summary=live_config_summary,
            authenticated_polymarket_connector_scaffold=authenticated_connector,
            authenticated_polymarket_connector_scaffold_summary=authenticated_connector_summary,
            wallet_signing_boundary_report=wallet_boundary,
            wallet_signing_boundary_summary=wallet_boundary_summary,
            signed_order_payload_validation_gate=signed_payload_gate,
            signed_order_payload_validation_gate_summary=signed_payload_gate_summary,
            tiny_live_canary_gonogo_gate=gonogo_summary,
            generated_at=generated_at,
        )
    )
    evidence_summary = dict(
        readiness_evidence_bundle_summary
        or summarize_live_canary_readiness_evidence_bundle(evidence_bundle, generated_at=generated_at)
    )
    replay_acceptance = dict(
        canary_replay_acceptance
        or {
            "contract_version": "pmbot_live_canary_acceptance_matrix.v1",
            "status": "passed",
            "review_only": True,
            "execution_enabling": False,
            "live_execution_approved": False,
            "canary_executable_now": False,
        }
    )
    risk_summary = _risk_cap_readiness_summary(risk_cap_readiness_summary)
    telegram_control = _telegram_operator_controls_summary(telegram_operator_control_bot_summary)
    telegram_mini_app = _telegram_mini_app_summary(telegram_mini_app_operator_panel_summary)
    unresolved_blockers = _unresolved_blocker_rows(matrix)
    sections = [
        _section(
            "live_enablement_config_status",
            "Live enablement config status",
            clean_text(live_config_summary.get("status") or live_config.get("status") or "not_available"),
            paths.get("live_enablement_config_preflight", ""),
            "Review the live enablement config preflight. It cannot enable execution in this task.",
            {
                "future_live_requested": live_config_summary.get("future_live_requested") is True,
                "dry_run_review_allowed": live_config_summary.get("dry_run_review_allowed") is True,
                "top_blocked_reasons": list(live_config_summary.get("top_blocked_reasons", []))[:5],
            },
        ),
        _section(
            "authenticated_connector_scaffold_status",
            "Authenticated connector scaffold status",
            clean_text(
                authenticated_connector_summary.get("status")
                or authenticated_connector.get("status")
                or "REVIEW_ONLY"
            ),
            paths.get("authenticated_polymarket_connector_scaffold", ""),
            "Review the authenticated connector scaffold. Authenticated calls and order submission remain disabled.",
            {
                "credentials_redacted_or_missing_only": (
                    authenticated_connector_summary.get("credentials_redacted_or_missing_only") is not False
                ),
                "network_calls_enabled": False,
                "authenticated_calls_enabled": False,
            },
        ),
        _section(
            "wallet_signing_boundary_status",
            "Wallet/signing boundary status",
            clean_text(wallet_boundary_summary.get("status") or wallet_boundary.get("status") or "SIGNING_DISABLED_REVIEW_ONLY"),
            paths.get("wallet_signing_boundary", ""),
            "Review the wallet/signing boundary. It refuses all signing and wallet access.",
            {
                "wallet_address_status": clean_text(wallet_boundary_summary.get("wallet_address_status") or "missing"),
                "signing_provider_status": clean_text(wallet_boundary_summary.get("signing_provider_status") or "missing"),
            },
        ),
        _section(
            "signed_order_payload_validation_gate_status",
            "Signed order payload validation gate status",
            clean_text(
                signed_payload_gate_summary.get("payload_shape_status")
                or signed_payload_gate_summary.get("status")
                or signed_payload_gate.get("status")
                or "SIGNING_DISABLED_REVIEW_ONLY"
            ),
            paths.get("signed_order_payload_validation_gate", ""),
            "Review payload shape only. The gate never signs, creates signed payloads, or creates signed orders.",
            {
                "payload_shape_review_ready": signed_payload_gate_summary.get("payload_shape_review_ready") is True,
                "top_blocked_reasons": list(signed_payload_gate_summary.get("top_blocked_reasons", []))[:5],
            },
        ),
        _section(
            "risk_cap_readiness_status",
            "Risk cap/readiness status",
            clean_text(risk_summary.get("risk_control_plane_status") or "review_only"),
            paths.get("btc_risk_decision", "") or paths.get("risk_limit_control_plane", ""),
            "Review market scope, max stake, daily loss, exposure, and one-shot canary constraints.",
            risk_summary,
        ),
        _section(
            "gonogo_status",
            "Go/no-go status",
            clean_text(gonogo_summary.get("status") or gonogo.get("status") or "NO_GO_UNRESOLVED_BLOCKERS"),
            paths.get("tiny_live_canary_gonogo_gate", ""),
            "Review the final go/no-go gate. It remains NO_GO and cannot approve live execution.",
            {
                "overall_decision": clean_text(gonogo_summary.get("overall_decision") or "NO_GO"),
                "resolved_blocker_count": 0,
                "unresolved_blocker_count": int(gonogo_summary.get("unresolved_blocker_count", 0) or 0),
            },
        ),
        _section(
            "evidence_bundle_status",
            "Evidence bundle status",
            clean_text(
                evidence_summary.get("readiness_evidence_bundle_status")
                or evidence_bundle.get("bundle_status")
                or "not_available"
            ),
            paths.get("readiness_evidence_bundle", ""),
            "Review the readiness evidence bundle. It is review evidence only and not live approval.",
            {
                "evidence_item_count": int(evidence_summary.get("evidence_item_count", 0) or 0),
                "missing_required_evidence_count": int(evidence_summary.get("missing_required_evidence_count", 0) or 0),
                "readiness_evidence_bundle_is_not_live_approval": True,
            },
        ),
        _section(
            "replay_acceptance_status",
            "Replay acceptance status",
            clean_text(replay_acceptance.get("status") or matrix.get("status") or "passed"),
            paths.get("live_connector_audit_replay", "") or paths.get("canary_replay_acceptance", ""),
            "Review replay acceptance and blocker matrix results. Replay is not execution.",
            {
                "blocker_matrix_status": clean_text(matrix.get("status") or "passed"),
                "all_blockers_unresolved": matrix.get("all_blockers_unresolved") is not False,
            },
        ),
        _section(
            "telegram_operator_controls_status",
            "Telegram operator controls status",
            clean_text(telegram_control.get("status") or "review_only"),
            paths.get("telegram_operator_control_state", ""),
            "Review Telegram controls as local markers only. They do not approve live execution.",
            telegram_control,
        ),
        _section(
            "telegram_mini_app_review_only_status",
            "Mini App review-only status",
            clean_text(telegram_mini_app.get("status") or "static_review_only"),
            paths.get("telegram_mini_app_operator_panel_html", "")
            or paths.get("telegram_mini_app_operator_panel_json", ""),
            "Review the Mini App as a static review-only surface with no executable live action.",
            telegram_mini_app,
        ),
        _section(
            "unresolved_blockers",
            "Unresolved blockers",
            "unresolved_blockers_present",
            paths.get("live_connector_blocker_matrix", "") or "live_connector_blocker_matrix:generated",
            "All live blockers remain unresolved. This packet resolves none of them.",
            {
                "unresolved_blocker_count": len(unresolved_blockers),
                "resolved_blocker_count": 0,
                "top_unresolved_blocker_ids": [row["blocker_id"] for row in unresolved_blockers[:8]],
            },
        ),
    ]
    artifact_manifest = _artifact_review_manifest(paths, sections)
    packet = {
        "contract_version": SUPERVISED_TINY_CANARY_APPROVAL_PACKET_CONTRACT,
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "packet_name": PACKET_NAME,
        "packet_id": _stable_id(
            "supervised-tiny-canary-approval-packet-051",
            {
                "section_statuses": [(section["section_id"], section["status"]) for section in sections],
                "artifact_references": [row["reference_path_or_id"] for row in artifact_manifest],
                "unresolved_blocker_count": len(unresolved_blockers),
            },
        ),
        "status": STATUS_REVIEW_READY_BLOCKED,
        "generated_at": generated_at,
        "review_only": True,
        "approval_packet_ready_for_human_review": True,
        "approval_packet_may_be_used_as_live_approval": False,
        "packet_cannot_be_interpreted_as_live_approval": True,
        "operator_must_not_execute_from_this_packet": True,
        "future_live_enabling_task_required": True,
        "refusal_safety_text": REFUSAL_SAFETY_TEXT,
        "sections": sections,
        "required_section_ids": list(REQUIRED_SECTION_IDS),
        "section_count": len(sections),
        "artifact_review_manifest": artifact_manifest,
        "operator_checklist": _operator_checklist(),
        "future_required_actions": _future_required_actions(),
        "unresolved_blockers": unresolved_blockers,
        "unresolved_blocker_count": len(unresolved_blockers),
        "resolved_blocker_count": 0,
        "execution_artifact_absence": _execution_artifact_absence(),
        "fake_execution_artifacts_emitted": False,
        "secret_or_raw_credential_fields_present": False,
        "raw_credentials_printed_or_persisted": False,
        "safety_summary": trading_core_safety_summary(),
    }
    packet.update(_packet_safety_flags())
    validation = validate_supervised_tiny_canary_approval_packet(packet, generated_at=generated_at)
    packet["validation"] = validation
    return packet


def summarize_supervised_tiny_canary_approval_packet(
    packet: Mapping[str, Any] | None = None,
    *,
    latest_supervised_tiny_canary_approval_packet_json_path: str = "",
    latest_supervised_tiny_canary_approval_packet_md_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(packet or build_supervised_tiny_canary_approval_packet(generated_at=generated_at))
    validation = (
        dict(value.get("validation", {}))
        if isinstance(value.get("validation"), Mapping)
        else validate_supervised_tiny_canary_approval_packet(value, generated_at=generated_at)
    )
    summary = {
        "contract_version": SUPERVISED_TINY_CANARY_APPROVAL_PACKET_SUMMARY_CONTRACT,
        "summary_id": _stable_id(
            "supervised-tiny-canary-approval-packet-summary-051",
            {
                "packet_id": value.get("packet_id"),
                "status": value.get("status"),
                "json_path": clean_text(latest_supervised_tiny_canary_approval_packet_json_path),
                "md_path": clean_text(latest_supervised_tiny_canary_approval_packet_md_path),
            },
        ),
        "schema_version": SCHEMA_VERSION,
        "packet_name": PACKET_NAME,
        "packet_id": clean_text(value.get("packet_id")),
        "status": clean_text(value.get("status") or STATUS_REVIEW_READY_BLOCKED),
        "supervised_tiny_canary_approval_packet_section_ready": True,
        "approval_packet_ready_for_human_review": value.get("approval_packet_ready_for_human_review") is True,
        "packet_cannot_be_interpreted_as_live_approval": True,
        "approval_packet_may_be_used_as_live_approval": False,
        "operator_must_not_execute_from_this_packet": True,
        "future_live_enabling_task_required": True,
        "section_count": int(value.get("section_count", 0) or 0),
        "operator_checklist_count": len(mapping_rows(value.get("operator_checklist"))),
        "future_required_action_count": len(mapping_rows(value.get("future_required_actions"))),
        "unresolved_blocker_count": int(value.get("unresolved_blocker_count", 0) or 0),
        "resolved_blocker_count": 0,
        "validation_status": clean_text(validation.get("status") or "blocked"),
        "validation_valid": validation.get("valid") is True,
        "latest_supervised_tiny_canary_approval_packet_json_path": clean_text(
            latest_supervised_tiny_canary_approval_packet_json_path
        ),
        "latest_supervised_tiny_canary_approval_packet_md_path": clean_text(
            latest_supervised_tiny_canary_approval_packet_md_path
        ),
        "no_executable_action": True,
    }
    summary.update(_packet_safety_flags())
    secret_validation = validate_secret_boundary_supervised_tiny_canary_approval_packet_summary(
        summary,
        generated_at=generated_at,
    )
    summary["secret_boundary_validation"] = secret_validation
    return summary


def validate_supervised_tiny_canary_approval_packet(
    packet: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    errors: list[str] = []
    statuses: list[str] = []
    value = dict(packet)

    if value.get("contract_version") != SUPERVISED_TINY_CANARY_APPROVAL_PACKET_CONTRACT:
        errors.append(f"contract_version must be {SUPERVISED_TINY_CANARY_APPROVAL_PACKET_CONTRACT}")
        statuses.append(VALIDATION_STATUS_INVALID_CONTRACT)
    if value.get("review_only") is not True:
        errors.append("review_only must be true")
        statuses.append(VALIDATION_STATUS_APPROVAL_INTERPRETATION)
    if value.get("approval_packet_may_be_used_as_live_approval") is not False:
        errors.append("approval_packet_may_be_used_as_live_approval must be false")
        statuses.append(VALIDATION_STATUS_APPROVAL_INTERPRETATION)
    if value.get("packet_cannot_be_interpreted_as_live_approval") is not True:
        errors.append("packet_cannot_be_interpreted_as_live_approval must be true")
        statuses.append(VALIDATION_STATUS_APPROVAL_INTERPRETATION)
    if value.get("operator_must_not_execute_from_this_packet") is not True:
        errors.append("operator_must_not_execute_from_this_packet must be true")
        statuses.append(VALIDATION_STATUS_APPROVAL_INTERPRETATION)
    for field in REQUIRED_FALSE_FLAGS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append(VALIDATION_STATUS_UNSAFE_FLAG)
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
        statuses.append(VALIDATION_STATUS_RESOLVED_BLOCKER)
    section_ids = {clean_text(row.get("section_id")) for row in mapping_rows(value.get("sections"))}
    for section_id in REQUIRED_SECTION_IDS:
        if section_id not in section_ids:
            errors.append(f"missing section {section_id}")
            statuses.append(VALIDATION_STATUS_MISSING_SECTION)
    for row in mapping_rows(value.get("future_required_actions")):
        if row.get("executable_in_this_task") is not False or row.get("implemented_in_this_task") is not False:
            errors.append("future_required_actions must remain non-executable and unimplemented in this task")
            statuses.append(VALIDATION_STATUS_FUTURE_ACTION_EXECUTABLE)
    artifact_keys = _forbidden_execution_artifact_key_paths(value)
    if artifact_keys:
        errors.append("forbidden execution artifact keys present")
        statuses.append(VALIDATION_STATUS_FAKE_EXECUTION_ARTIFACT)
    if value.get("fake_execution_artifacts_emitted") is not False:
        errors.append("fake_execution_artifacts_emitted must be false")
        statuses.append(VALIDATION_STATUS_FAKE_EXECUTION_ARTIFACT)
    secret_validation = validate_secret_boundary_supervised_tiny_canary_approval_packet(
        value,
        generated_at=generated_at,
    )
    forbidden_secret_paths = list(secret_validation.get("forbidden_secret_field_paths", []))
    if secret_validation.get("valid") is not True:
        errors.append("approval packet violates static secret boundary")
        statuses.append(VALIDATION_STATUS_SECRET_BOUNDARY)

    valid = not errors
    statuses = [VALIDATION_STATUS_VALID] if valid else _dedupe(statuses)
    status = VALIDATION_STATUS_VALID if valid else statuses[0]
    return {
        "contract_version": SUPERVISED_TINY_CANARY_APPROVAL_PACKET_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "supervised-tiny-canary-approval-packet-validation-051",
            {
                "packet_id": value.get("packet_id"),
                "errors": errors,
                "statuses": statuses,
                "forbidden_execution_artifact_key_paths": artifact_keys,
                "forbidden_secret_field_paths": forbidden_secret_paths,
            },
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": status,
        "statuses": statuses,
        "errors": errors,
        "forbidden_execution_artifact_key_paths": artifact_keys,
        "forbidden_secret_field_paths": forbidden_secret_paths,
        "secret_boundary_validation": secret_validation,
        "review_only": True,
        "approval_packet_may_be_used_as_live_approval": False,
        "packet_cannot_be_interpreted_as_live_approval": True,
        "resolved_blocker_count": 0,
        **_packet_safety_flags(),
    }


def render_supervised_tiny_canary_approval_packet_json(packet: Mapping[str, Any]) -> str:
    return json.dumps(dict(packet), indent=2, sort_keys=True) + "\n"


def render_supervised_tiny_canary_approval_packet_markdown(packet: Mapping[str, Any]) -> str:
    rows = [
        "# Supervised Tiny Canary Runbook And Operator Approval Packet",
        "",
        "## Safety Status",
        "",
        f"- Status: `{packet.get('status')}`",
        "- Review only: `true`",
        "- Live execution approved: `false`",
        "- Canary executable now: `false`",
        "- Real execution available: `false`",
        "- This packet does not approve or enable live execution.",
        "",
        "## Required False Flags",
        "",
        *[
            f"- `{field}`: `{str(packet.get(field)).lower()}`"
            for field in (
                "authenticated_polymarket_enabled",
                "live_connector_enabled",
                "order_submission_enabled",
                "wallet_signing_enabled",
                "signing_enabled",
                "signed_payload_generation_enabled",
                "signed_order_generation_enabled",
                "allowed_for_live",
                "canary_executable_now",
                "live_execution_approved",
                "real_execution_available",
                "resolved_blocker_count",
            )
        ],
        "",
        "## Review Sections",
        "",
    ]
    for section in mapping_rows(packet.get("sections")):
        rows.extend(
            [
                f"### {section.get('title')}",
                "",
                f"- Section ID: `{section.get('section_id')}`",
                f"- Status: `{section.get('status')}`",
                f"- Artifact: `{section.get('artifact_reference')}`",
                f"- Execution enabling: `{str(section.get('execution_enabling')).lower()}`",
                f"- Live approval: `{str(section.get('live_approval')).lower()}`",
                f"- Notes: {section.get('operator_review_notes')}",
                "",
            ]
        )
    rows.extend(
        [
            "## Operator Checklist",
            "",
            *bullet_lines(row.get("text", "") for row in mapping_rows(packet.get("operator_checklist"))),
            "",
            "## Future Required Actions",
            "",
            *bullet_lines(row.get("description", "") for row in mapping_rows(packet.get("future_required_actions"))),
            "",
            "## Artifacts To Inspect",
            "",
            *bullet_lines(
                f"{row.get('artifact_label')}: `{row.get('reference_path_or_id')}`"
                for row in mapping_rows(packet.get("artifact_review_manifest"))
            ),
            "",
            "## Refusal Text",
            "",
            clean_text(packet.get("refusal_safety_text")),
            "",
        ]
    )
    markdown = "\n".join(rows)
    validation = validate_secret_boundary_supervised_tiny_canary_approval_packet_markdown(
        markdown,
        generated_at=clean_text(packet.get("generated_at")) or GENERATED_AT,
    )
    if validation.get("valid") is not True:
        raise ValueError(f"rendered markdown violates static secret boundary: {validation.get('errors')}")
    return markdown


def _section(
    section_id: str,
    title: str,
    status: str,
    artifact_reference: str,
    operator_review_notes: str,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    value = {
        "section_id": section_id,
        "title": title,
        "status": clean_text(status) or "not_available",
        "artifact_reference": clean_text(artifact_reference) or f"{section_id}:current-run",
        "operator_review_notes": operator_review_notes,
        "details": dict(details or {}),
        "review_ready": True,
        "review_only": True,
        "live_approval": False,
        "execution_enabling": False,
        "no_executable_action": True,
    }
    value.update(_packet_safety_flags())
    return value


def _operator_checklist() -> list[dict[str, Any]]:
    return [
        {
            "check_id": check_id,
            "text": text,
            "operator_confirmed": False,
            "status": "pending_manual_operator_review",
            "required_before_any_future_live_enabling_task": True,
            "live_approval": False,
            "execution_enabling": False,
            "no_executable_action": True,
        }
        for check_id, text in OPERATOR_CHECKLIST_ITEMS
    ]


def _future_required_actions() -> list[dict[str, Any]]:
    return [
        {
            "action_id": action_id,
            "description": description,
            "requires_separate_operator_approved_task": True,
            "implemented_in_this_task": False,
            "executable_in_this_task": False,
            "live_approval": False,
            "execution_enabling": False,
        }
        for action_id, description in FUTURE_REQUIRED_ACTIONS
    ]


def _artifact_review_manifest(
    paths: Mapping[str, str],
    sections: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section in sections:
        rows.append(
            {
                "artifact_id": clean_text(section.get("section_id")),
                "artifact_label": clean_text(section.get("title")),
                "reference_path_or_id": clean_text(section.get("artifact_reference")),
                "operator_must_inspect": True,
                "review_only": True,
                "live_approval": False,
                "execution_enabling": False,
            }
        )
    for key in (
        "operator_ui_panel_json",
        "operator_ui_panel_md",
        "operator_ui_panel_html",
        "supervised_tiny_canary_approval_packet_json",
        "supervised_tiny_canary_approval_packet_md",
    ):
        if clean_text(paths.get(key)):
            rows.append(
                {
                    "artifact_id": key,
                    "artifact_label": key.replace("_", " "),
                    "reference_path_or_id": clean_text(paths.get(key)),
                    "operator_must_inspect": True,
                    "review_only": True,
                    "live_approval": False,
                    "execution_enabling": False,
                }
            )
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        key = f"{row['artifact_id']}::{row['reference_path_or_id']}"
        if key not in seen:
            seen.add(key)
            deduped.append(row)
    return deduped


def _risk_cap_readiness_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(value or {})
    summary = {
        "risk_control_plane_status": clean_text(source.get("risk_control_plane_status") or source.get("status") or "review_only"),
        "max_order_notional_usd": source.get("max_order_notional_usd", "not_available"),
        "max_daily_loss_usd": source.get("max_daily_loss_usd", "not_available"),
        "max_total_exposure_usd": source.get("max_total_exposure_usd", "not_available"),
        "max_trades_per_day": source.get("max_trades_per_day", source.get("max_orders_per_day", "not_available")),
        "allowed_for_dry_run": source.get("allowed_for_dry_run") is True,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "execution_enabling": False,
    }
    return summary


def _telegram_operator_controls_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(value or {})
    return {
        "status": clean_text(source.get("status") or source.get("review_only_status") or "review_only"),
        "configured": source.get("configured") is True,
        "telegram_bot_token_status": clean_text(source.get("telegram_bot_token_status") or "not_configured_redacted"),
        "allowed_operator_ids_configured": source.get("allowed_operator_ids_configured") is True,
        "allowed_operator_id_count": int(source.get("allowed_operator_id_count", 0) or 0),
        "operator_pause_requested": source.get("operator_pause_requested") is True,
        "operator_kill_switch_requested": source.get("operator_kill_switch_requested") is True,
        "raw_telegram_bot_token_exposed": False,
        "raw_operator_user_ids_exposed": False,
        "review_only": True,
        "live_approval": False,
        "execution_enabling": False,
        "order_submission_enabled": False,
    }


def _telegram_mini_app_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(value or {})
    return {
        "status": clean_text(source.get("status") or "static_review_only"),
        "panel_artifact_available": source.get("panel_artifact_available") is True,
        "review_only": True,
        "live_actions_available": False,
        "execution_enabling": False,
        "live_approval": False,
        "order_submission_enabled": False,
        "telegram_init_data_status": clean_text(source.get("telegram_init_data_status") or "not_configured_redacted"),
        "raw_telegram_init_data_exposed": False,
        "raw_operator_user_ids_exposed": False,
    }


def _unresolved_blocker_rows(blocker_matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in mapping_rows(blocker_matrix.get("blockers")):
        if clean_text(row.get("resolution_status") or "unresolved") == "resolved":
            continue
        rows.append(
            {
                "blocker_id": clean_text(row.get("blocker_id")),
                "blocker_category": clean_text(row.get("blocker_category") or row.get("blocker_name")),
                "current_status": clean_text(row.get("current_status") or "unresolved"),
                "resolution_status": "unresolved",
                "severity": clean_text(row.get("severity") or "critical"),
                "why_it_blocks_live_execution": clean_text(
                    row.get("why_it_blocks_live_execution") or "This blocker remains unresolved."
                ),
            }
        )
    if rows:
        return rows
    return [
        {
            "blocker_id": "PMBOT-LIVE-BLOCKER-051-DEFAULT",
            "blocker_category": "live_execution_still_disabled",
            "current_status": "unresolved",
            "resolution_status": "unresolved",
            "severity": "critical",
            "why_it_blocks_live_execution": "The packet is review-only and cannot enable live execution.",
        }
    ]


def _execution_artifact_absence() -> dict[str, Any]:
    return {
        "signature_present": False,
        "signed_payload_present": False,
        "signed_order_present": False,
        "transaction_hash_present": False,
        "order_id_present": False,
        "fill_present": False,
        "execution_result_present": False,
        "no_signature_returned": True,
        "no_signed_payload_returned": True,
        "no_signed_order_returned": True,
        "no_transaction_hash_returned": True,
        "no_order_id_returned": True,
        "no_fill_returned": True,
        "no_execution_result_returned": True,
        "no_fake_signature_generated": True,
        "no_fake_signed_payload_generated": True,
        "no_fake_signed_order_generated": True,
        "no_fake_order_id_generated": True,
        "no_fake_transaction_hash_generated": True,
        "no_fake_fill_generated": True,
        "no_fake_execution_result_generated": True,
    }


def _packet_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "passive_artifact_only": True,
        "manual_review_only": True,
        "review_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "execution_enabling": False,
        "no_executable_action": True,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "network_used": False,
        "network_calls_enabled": False,
        "external_api_calls_performed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_calls_enabled": False,
        "authenticated_endpoints_enabled": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
        "would_submit_order": False,
        "wallet_signing_enabled": False,
        "wallet_enabled": False,
        "real_wallet_used": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "transaction_signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "real_signature_created": False,
        "real_order_submitted": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_execution_allowed": False,
        "live_execution_enabled": False,
        "live_execution_performed": False,
        "live_approval": False,
        "live_action_exposed": False,
        "resolved_blocker_count": 0,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def _forbidden_execution_artifact_key_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            normalized = key_text.lower()
            nested_path = f"{path}.{key_text}"
            if normalized in FORBIDDEN_EXECUTION_ARTIFACT_KEYS:
                paths.append(nested_path)
            paths.extend(_forbidden_execution_artifact_key_paths(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(_forbidden_execution_artifact_key_paths(nested, f"{path}[{index}]"))
    return paths


def mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
