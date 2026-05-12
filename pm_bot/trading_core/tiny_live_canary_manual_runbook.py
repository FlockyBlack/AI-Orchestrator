from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, trading_core_safety_summary

TINY_LIVE_CANARY_MANUAL_RUNBOOK_CONTRACT = "pmbot_tiny_live_canary_manual_runbook.v1"
TINY_LIVE_CANARY_RUNBOOK_SECTION_CONTRACT = "pmbot_tiny_live_canary_runbook_section.v1"
TINY_LIVE_CANARY_RUNBOOK_STEP_CONTRACT = "pmbot_tiny_live_canary_runbook_step.v1"
TINY_LIVE_CANARY_RUNBOOK_VALIDATION_CONTRACT = "pmbot_tiny_live_canary_runbook_validation.v1"

MANUAL_RUNBOOK_STATUS_READY = "manual_runbook_ready_for_future_review_only"
MANUAL_RUNBOOK_STATUS_BLOCKED = "manual_runbook_blocked"
NON_EXECUTION_STATEMENT = (
    "This runbook is a manual preflight review artifact only; this build does not authorize live execution "
    "and does not perform live execution."
)

REQUIRED_SECTION_IDS = (
    "purpose_and_scope",
    "explicit_non_execution_statement",
    "prerequisite_artifacts",
    "operator_identity_responsibility",
    "market_selection_review",
    "risk_review",
    "secret_boundary_review",
    "disabled_connector_review",
    "audit_replay_review",
    "operator_packet_review",
    "operator_intent_packet_review",
    "readiness_evidence_bundle_review",
    "kill_switch_verification",
    "maximum_exposure_limits",
    "manual_pause_abort_conditions",
    "evidence_capture_checklist",
    "post_canary_review_requirements",
    "rollback_incident_notes",
    "final_non_authorization_statement",
)


@dataclass(frozen=True)
class TinyLiveCanaryRunbookStep:
    step_id: str
    title: str
    instruction: str
    required: bool = True
    produces_evidence: bool = False
    operator_confirmation_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_RUNBOOK_STEP_CONTRACT
        value["live_execution_approved"] = False
        value["real_execution_available"] = False
        value["canary_executable_now"] = False
        value["local_artifact_only"] = True
        value["manual_review_only"] = True
        return value


@dataclass(frozen=True)
class TinyLiveCanaryRunbookSection:
    section_id: str
    title: str
    summary: str
    steps: tuple[TinyLiveCanaryRunbookStep, ...]
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_RUNBOOK_SECTION_CONTRACT
        value["steps"] = [step.to_dict() for step in self.steps]
        value["live_execution_approved"] = False
        value["real_execution_available"] = False
        value["canary_executable_now"] = False
        value["local_artifact_only"] = True
        value["manual_review_only"] = True
        return value


@dataclass(frozen=True)
class TinyLiveCanaryManualRunbook:
    runbook_id: str
    status: str
    sections: tuple[TinyLiveCanaryRunbookSection, ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_MANUAL_RUNBOOK_CONTRACT
        value["sections"] = [section.to_dict() for section in self.sections]
        value["section_count"] = len(self.sections)
        value["required_section_ids"] = list(REQUIRED_SECTION_IDS)
        value["manual_runbook_ready"] = self.status == MANUAL_RUNBOOK_STATUS_READY
        value["non_execution_statement"] = NON_EXECUTION_STATEMENT
        value["final_non_authorization_statement"] = NON_EXECUTION_STATEMENT
        value["pure_data_text_generation_only"] = True
        value["manual_only_preflight_process"] = True
        value["operator_review_is_not_live_approval"] = True
        value.update(_runbook_safety_flags())
        value["safety_summary"] = trading_core_safety_summary()
        return value


@dataclass(frozen=True)
class TinyLiveCanaryRunbookValidationResult:
    validation_id: str
    valid: bool
    errors: tuple[str, ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_RUNBOOK_VALIDATION_CONTRACT
        value["errors"] = list(self.errors)
        value["status"] = "passed" if self.valid else "blocked"
        value["manual_runbook_ready"] = self.valid
        value.update(_runbook_safety_flags())
        return value


def build_tiny_live_canary_manual_runbook(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    sections = tuple(
        [
            _section(
                "purpose_and_scope",
                "Purpose And Scope",
                "Define the manual evidence review required before a future tiny canary could be proposed.",
                [
                    _step(
                        "confirm_scope",
                        "Confirm review scope",
                        "Confirm this artifact covers preflight review only and leaves current PMBOT execution disabled.",
                    ),
                    _step(
                        "confirm_future_shape",
                        "Confirm future canary shape",
                        "Confirm the future canary shape is one reviewed market, one reviewed order-sized action, and tiny fixed exposure limits.",
                    ),
                ],
            ),
            _section(
                "explicit_non_execution_statement",
                "Explicit Non-Execution Statement",
                NON_EXECUTION_STATEMENT,
                [
                    _step(
                        "record_non_execution_acknowledgement",
                        "Record non-execution acknowledgement",
                        "Record that no live connector, wallet access, signing, authenticated endpoint call, or real order placement is authorized.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "prerequisite_artifacts",
                "Prerequisite Artifacts",
                "List the local artifacts that must exist before a future proposal is reviewed.",
                [
                    _step(
                        "check_preflight_contract",
                        "Check preflight contract",
                        "Confirm the tiny live canary preflight contract artifact exists and validates.",
                        produces_evidence=True,
                    ),
                    _step(
                        "check_operator_packet",
                        "Check operator packet",
                        "Confirm the operator review packet exists and still states that review is not live approval.",
                        produces_evidence=True,
                    ),
                    _step(
                        "check_audit_replay",
                        "Check audit replay",
                        "Confirm the disabled connector audit replay exists and remains deterministic and non-executable.",
                        produces_evidence=True,
                    ),
                    _step(
                        "check_secret_boundary",
                        "Check secret boundary",
                        "Confirm static secret-boundary validation exists without reading or requesting real secrets.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "operator_identity_responsibility",
                "Operator Identity And Responsibility",
                "Reserve a manual placeholder for the operator who would own any future review.",
                [
                    _step(
                        "record_operator_placeholder",
                        "Record operator placeholder",
                        "Record operator identity, review time, and responsibility statement in a future evidence packet.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "market_selection_review",
                "Market Selection Review",
                "Require a manual review of the single market candidate without treating analysis as trading advice.",
                [
                    _step(
                        "verify_single_market",
                        "Verify single market",
                        "Confirm the future canary proposal references exactly one manually reviewed market.",
                        produces_evidence=True,
                    ),
                    _step(
                        "verify_no_signal_language",
                        "Verify no signal language",
                        "Confirm artifacts do not present side selection, probability, edge, or confidence as actionable real trading guidance.",
                    ),
                ],
            ),
            _section(
                "risk_review",
                "Risk Review",
                "Require manual review of fixed tiny limits and unresolved blockers.",
                [
                    _step(
                        "verify_limit_policy",
                        "Verify limit policy",
                        "Confirm max_market_count is 1, max_order_count is 1, max_position_size_usd is tiny, and max_total_notional_usd is tiny.",
                        produces_evidence=True,
                    ),
                    _step(
                        "verify_blocker_matrix",
                        "Verify blocker matrix",
                        "Confirm live connector blockers remain unresolved and are not treated as approval conditions.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "secret_boundary_review",
                "Secret Boundary Review",
                "Confirm the build remains static and does not inspect, print, persist, or request secrets.",
                [
                    _step(
                        "verify_no_secret_access",
                        "Verify no secret access",
                        "Confirm no private-key, mnemonic, credential, wallet password, or token material appears in artifacts.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "disabled_connector_review",
                "Disabled Connector Review",
                "Confirm any connector-shaped artifact is refusal-only and remains disabled.",
                [
                    _step(
                        "verify_disabled_connector",
                        "Verify disabled connector",
                        "Confirm the real wallet connector disabled adapter reports disabled status and unavailable real execution.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "audit_replay_review",
                "Audit Replay Review",
                "Confirm replay is deterministic, local, and non-executable.",
                [
                    _step(
                        "verify_replay_status",
                        "Verify replay status",
                        "Confirm replay status is passively reviewed and no live connector is enabled.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "operator_packet_review",
                "Operator Packet Review",
                "Confirm the operator packet is only a review packet.",
                [
                    _step(
                        "verify_review_not_approval",
                        "Verify review is not approval",
                        "Confirm operator_review_is_not_live_approval is true and live_execution_approved is false.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "operator_intent_packet_review",
                "Operator Intent Packet Review",
                "Confirm the dry-run operator intent packet is a human acknowledgement artifact only.",
                [
                    _step(
                        "verify_intent_packet_not_live_approval",
                        "Verify intent packet is not live approval",
                        "Confirm operator_intent_is_not_live_approval is true and live_execution_approved is false.",
                        produces_evidence=True,
                    ),
                    _step(
                        "verify_signed_means_human_acknowledgement",
                        "Verify signed means human acknowledgement",
                        "Confirm operator-signed intent terminology is plain human acknowledgement only, not cryptographic signing.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "readiness_evidence_bundle_review",
                "Readiness Evidence Bundle Review",
                "Confirm the dry-run readiness evidence bundle links artifacts for review only and is not live approval.",
                [
                    _step(
                        "verify_evidence_bundle_review_only",
                        "Verify evidence bundle is review-only",
                        "Confirm readiness_evidence_bundle_is_not_live_approval is true and live_execution_approved is false.",
                        produces_evidence=True,
                    ),
                    _step(
                        "verify_evidence_bundle_does_not_resolve_blockers",
                        "Verify blockers remain unresolved",
                        "Confirm the bundle summarizes unresolved live blockers without reducing severity or making the canary executable.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "kill_switch_verification",
                "Kill-Switch Verification",
                "Define the kill-switch checks required before any future proposal could proceed.",
                [
                    _step(
                        "verify_visible_stop_control",
                        "Verify visible stop control",
                        "Confirm a future operator-visible stop control is documented.",
                        produces_evidence=True,
                    ),
                    _step(
                        "verify_dry_run_stop_simulation",
                        "Verify dry-run stop simulation",
                        "Confirm a dry-run kill-switch simulation is required before any future gated task.",
                        produces_evidence=True,
                    ),
                    _step(
                        "verify_no_bypass",
                        "Verify no bypass",
                        "Confirm no scheduler, daemon, or autonomous loop may bypass the operator.",
                    ),
                ],
            ),
            _section(
                "maximum_exposure_limits",
                "Maximum Exposure Limits",
                "Document fixed tiny limits for a future proposal while leaving them non-executable.",
                [
                    _step(
                        "record_limit_acknowledgement",
                        "Record limit acknowledgement",
                        "Record that limits are placeholders for future gated review and do not make execution available.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "manual_pause_abort_conditions",
                "Manual Pause And Abort Conditions",
                "List manual conditions that require stopping the review.",
                [
                    _step(
                        "abort_on_missing_artifacts",
                        "Abort on missing artifacts",
                        "Stop review if any required artifact is missing, invalid, stale, or contradictory.",
                    ),
                    _step(
                        "abort_on_enabled_connector",
                        "Abort on enabled connector",
                        "Stop review if any artifact indicates live connector enabled, real execution available, or live execution approved.",
                    ),
                    _step(
                        "abort_on_secret_request",
                        "Abort on secret request",
                        "Stop review if any workflow asks for private keys, mnemonics, credentials, wallet access, signing, or endpoint authentication.",
                    ),
                ],
            ),
            _section(
                "evidence_capture_checklist",
                "Evidence Capture Checklist",
                "Define evidence that must be captured for future review.",
                [
                    _step(
                        "capture_contract_validation",
                        "Capture contract validation",
                        "Capture preflight contract validation output.",
                        produces_evidence=True,
                    ),
                    _step(
                        "capture_runbook_acknowledgement",
                        "Capture runbook acknowledgement",
                        "Capture manual runbook acknowledgement and non-execution statement.",
                        produces_evidence=True,
                    ),
                    _step(
                        "capture_blocker_snapshot",
                        "Capture blocker snapshot",
                        "Capture unresolved blocker matrix and kill-switch requirement packet.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "post_canary_review_requirements",
                "Post-Canary Review Requirements",
                "Define future review requirements without enabling a canary now.",
                [
                    _step(
                        "document_future_review",
                        "Document future review",
                        "Document expected future incident review, reconciliation, and evidence inventory before any separate gated task.",
                    ),
                ],
            ),
            _section(
                "rollback_incident_notes",
                "Rollback And Incident Notes",
                "Reserve manual incident notes and rollback evidence for future gated work.",
                [
                    _step(
                        "record_incident_placeholder",
                        "Record incident placeholder",
                        "Record where emergency stop notes, rollback notes, and operator observations would be captured.",
                        produces_evidence=True,
                    ),
                ],
            ),
            _section(
                "final_non_authorization_statement",
                "Final Non-Authorization Statement",
                NON_EXECUTION_STATEMENT,
                [
                    _step(
                        "confirm_no_execution_authorization",
                        "Confirm no execution authorization",
                        "Confirm this build still cannot execute a canary and requires a separate future gated task.",
                        produces_evidence=True,
                    ),
                ],
            ),
        ]
    )
    runbook = TinyLiveCanaryManualRunbook(
        runbook_id=_stable_id(
            "tiny-live-canary-manual-runbook-033",
            {"section_ids": [section.section_id for section in sections]},
        ),
        status=MANUAL_RUNBOOK_STATUS_READY,
        sections=sections,
        generated_at=generated_at,
    ).to_dict()
    validation = validate_tiny_live_canary_manual_runbook(runbook, generated_at=generated_at)
    runbook["validation"] = validation
    if validation.get("valid") is not True:
        runbook["status"] = MANUAL_RUNBOOK_STATUS_BLOCKED
        runbook["manual_runbook_ready"] = False
    return runbook


def validate_tiny_live_canary_manual_runbook(
    runbook: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    errors: list[str] = []
    if runbook.get("contract_version") != TINY_LIVE_CANARY_MANUAL_RUNBOOK_CONTRACT:
        errors.append(f"contract_version must be {TINY_LIVE_CANARY_MANUAL_RUNBOOK_CONTRACT}")
    section_ids = [
        clean_text(section.get("section_id"))
        for section in runbook.get("sections", [])
        if isinstance(section, Mapping)
    ]
    missing_sections = [section_id for section_id in REQUIRED_SECTION_IDS if section_id not in section_ids]
    if missing_sections:
        errors.append(f"missing required sections: {', '.join(missing_sections)}")
    full_text = json.dumps(runbook, sort_keys=True).lower()
    if NON_EXECUTION_STATEMENT.lower() not in full_text:
        errors.append("runbook must include the explicit non-execution statement")
    for required_phrase in (
        "kill-switch",
        "abort",
        "evidence capture",
        "does not authorize",
        "does not perform live execution",
    ):
        if required_phrase not in full_text:
            errors.append(f"runbook must include {required_phrase}")
    if runbook.get("manual_only_preflight_process") is not True:
        errors.append("manual_only_preflight_process must be true")
    if runbook.get("pure_data_text_generation_only") is not True:
        errors.append("pure_data_text_generation_only must be true")
    if runbook.get("operator_review_is_not_live_approval") is not True:
        errors.append("operator_review_is_not_live_approval must be true")
    for field in ("live_execution_approved", "real_execution_available", "canary_executable_now"):
        if runbook.get(field) is not False:
            errors.append(f"{field} must be false")
    return TinyLiveCanaryRunbookValidationResult(
        validation_id=_stable_id(
            "tiny-live-canary-runbook-validation-033",
            {"runbook_id": runbook.get("runbook_id"), "errors": errors},
        ),
        valid=not errors,
        errors=tuple(errors),
        generated_at=generated_at,
    ).to_dict()


def render_tiny_live_canary_manual_runbook_markdown(runbook: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Tiny Live Canary Manual Runbook",
        "",
        f"- Runbook: `{runbook.get('runbook_id')}`",
        f"- Status: `{runbook.get('status')}`",
        f"- Manual runbook ready: `{str(runbook.get('manual_runbook_ready')).lower()}`",
        f"- Canary executable now: `{str(runbook.get('canary_executable_now')).lower()}`",
        f"- Live execution approved: `{str(runbook.get('live_execution_approved')).lower()}`",
        f"- Real execution available: `{str(runbook.get('real_execution_available')).lower()}`",
        f"- Statement: {runbook.get('non_execution_statement')}",
        "",
    ]
    for section in runbook.get("sections", []):
        if not isinstance(section, Mapping):
            continue
        lines.extend(
            [
                f"## {section.get('title')}",
                "",
                str(section.get("summary")),
                "",
                *bullet_lines(
                    f"`{step.get('step_id')}` {step.get('title')}: {step.get('instruction')}"
                    for step in section.get("steps", [])
                    if isinstance(step, Mapping)
                ),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _section(
    section_id: str,
    title: str,
    summary: str,
    steps: Sequence[TinyLiveCanaryRunbookStep],
) -> TinyLiveCanaryRunbookSection:
    return TinyLiveCanaryRunbookSection(
        section_id=section_id,
        title=title,
        summary=summary,
        steps=tuple(steps),
    )


def _step(
    step_id: str,
    title: str,
    instruction: str,
    *,
    produces_evidence: bool = False,
) -> TinyLiveCanaryRunbookStep:
    return TinyLiveCanaryRunbookStep(
        step_id=step_id,
        title=title,
        instruction=instruction,
        produces_evidence=produces_evidence,
    )


def _runbook_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "passive_artifact_only": True,
        "manual_review_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "real_wallet_access_performed": False,
        "cryptographic_signing_performed": False,
        "real_order_placement_performed": False,
        "authenticated_endpoint_call_performed": False,
        "real_execution_available": False,
        "live_execution_approved": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "canary_executable_now": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
