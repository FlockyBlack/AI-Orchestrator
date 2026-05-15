from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-064-EXPLICIT-LIVE-CREDENTIALS-READINESS-GATE-NO-SECRETS"
DESIGN_REFERENCE_TASK_ID = "ORCH-PMBOT-TRADING-MVP-064-DESIGN-EXPLICIT-LIVE-CREDENTIALS-READINESS-GATE"

EXECUTION_MODE = "preflight"
MODE = "explicit live credentials readiness / redacted presence-only / review-only"

EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_CONTRACT = "pmbot_explicit_live_credentials_readiness_gate_064.v1"
EXPLICIT_LIVE_CREDENTIALS_READINESS_SUMMARY_CONTRACT = (
    "pmbot_explicit_live_credentials_readiness_summary_064.v1"
)
EXPLICIT_LIVE_CREDENTIAL_MARKER_REQUIREMENT_CONTRACT = (
    "pmbot_explicit_live_credential_marker_requirement_064.v1"
)
EXPLICIT_LIVE_CREDENTIAL_MARKER_PRESENCE_CONTRACT = (
    "pmbot_explicit_live_credential_marker_presence_064.v1"
)
EXPLICIT_LIVE_CREDENTIAL_MARKER_PRESENCE_REPORT_CONTRACT = (
    "pmbot_explicit_live_credential_marker_presence_report_064.v1"
)
EXPLICIT_LIVE_CREDENTIAL_OPERATOR_APPROVAL_BOUNDARY_CONTRACT = (
    "pmbot_explicit_live_credentials_operator_approval_boundary_064.v1"
)
EXPLICIT_LIVE_CREDENTIAL_SAFETY_POLICY_VALIDATION_CONTRACT = (
    "pmbot_explicit_live_credentials_safety_policy_validation_064.v1"
)
EXPLICIT_LIVE_CREDENTIAL_BLOCKER_CONTRACT = "pmbot_explicit_live_credentials_blocker_064.v1"
EXPLICIT_LIVE_CREDENTIAL_BLOCKER_MATRIX_CONTRACT = (
    "pmbot_explicit_live_credentials_blocker_matrix_064.v1"
)
EXPLICIT_LIVE_CREDENTIAL_OPERATOR_CHECKLIST_CONTRACT = (
    "pmbot_explicit_live_credentials_operator_checklist_064.v1"
)
LATEST_EXPLICIT_LIVE_CREDENTIALS_READINESS_STATUS_CONTRACT = (
    "pmbot_latest_explicit_live_credentials_readiness_status_064.v1"
)
EXPLICIT_LIVE_CREDENTIALS_READINESS_VALIDATION_CONTRACT = (
    "pmbot_explicit_live_credentials_readiness_validation_064.v1"
)

STATUS_BLOCKED = "blocked"
STATUS_REDACTED_PRESENCE_REVIEW_READY = "redacted_presence_review_ready_live_blocked"

MARKER_CATEGORY_MISSING = "missing"
MARKER_CATEGORY_PRESENT_REDACTED = "present_redacted"
MARKER_CATEGORY_EXECUTION_FLAG_BLOCKED = "conflicting_execution_flag_blocked"
MARKER_CATEGORY_NOT_CHECKED = "not_checked"

MARKER_GROUP_CREDENTIAL_SOURCE = "credential_source_marker"
MARKER_GROUP_MANUAL_CONTROL = "manual_control_marker"
MARKER_GROUP_EXECUTION_FLAG = "execution_flag_must_remain_blocked"
MARKER_GROUP_CONTEXT = "non_secret_context_marker"

DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"

CREDENTIAL_SOURCE_MARKERS = (
    "PMBOT_LIVE_CREDENTIALS_READINESS_GATE_ENABLED",
    "PMBOT_POLYMARKET_AUTH_CONFIG_PRESENT",
    "PMBOT_POLYMARKET_CLOB_BASE_URL",
    "PMBOT_POLYMARKET_L2_API_KEY_PRESENT",
    "PMBOT_POLYMARKET_L2_API_SECRET_PRESENT",
    "PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT",
    "PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED",
    "PMBOT_WALLET_ADDRESS_CONFIGURED",
    "PMBOT_SIGNING_PROVIDER_CONFIGURED",
    "PMBOT_SIGNING_DRY_RUN_ONLY",
)

MANUAL_CONTROL_MARKERS = (
    "PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL",
    "PMBOT_REQUIRE_KILL_SWITCH_READY",
    "PMBOT_LIVE_CREDENTIALS_OPERATOR_REVIEW_RECORD_PRESENT",
    "PMBOT_LIVE_CREDENTIALS_DUAL_CONTROL_REVIEW_PRESENT",
)

EXECUTION_FLAG_MARKERS = (
    "PMBOT_LIVE_MODE",
    "PMBOT_LIVE_CANARY_ENABLED",
    "PMBOT_AUTHENTICATED_POLYMARKET_ENABLED",
    "PMBOT_WALLET_SIGNING_ENABLED",
    "PMBOT_ORDER_SUBMISSION_ENABLED",
)

CONTEXT_MARKERS = (
    "PMBOT_MAX_ORDER_NOTIONAL_USD",
    "PMBOT_DAILY_LOSS_CAP_USD",
    "PMBOT_TOTAL_EXPOSURE_CAP_USD",
    "PMBOT_MAX_LIVE_TRADES_PER_DAY",
    "PMBOT_ALLOWED_MARKET_SLUGS",
    "PMBOT_ALLOWED_MARKET_IDS",
)

DEFAULT_MARKER_REQUIREMENTS = (
    *((name, MARKER_GROUP_CREDENTIAL_SOURCE, True) for name in CREDENTIAL_SOURCE_MARKERS),
    *((name, MARKER_GROUP_MANUAL_CONTROL, True) for name in MANUAL_CONTROL_MARKERS),
    *((name, MARKER_GROUP_EXECUTION_FLAG, False) for name in EXECUTION_FLAG_MARKERS),
    *((name, MARKER_GROUP_CONTEXT, False) for name in CONTEXT_MARKERS),
)

REQUIRED_UNRESOLVED_BLOCKER_IDS = (
    "live_execution_not_approved",
    "credentials_not_value_verified_by_pmbot",
    "operator_review_does_not_enable_execution",
    "authenticated_polymarket_requests_blocked",
    "wallet_connection_blocked",
    "signer_instantiation_blocked",
    "private_key_reads_blocked",
    "api_secret_reads_blocked",
    "signed_payload_generation_blocked",
    "order_submission_blocked",
    "order_cancellation_blocked",
    "balance_reads_blocked",
    "position_reads_blocked",
    "kill_switch_not_bound_to_live_adapter",
    "rollback_cancel_plan_not_implemented",
    "first_live_order_task_not_present",
)

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "operator_approved",
    "candidate_is_executable",
    "order_submission_enabled",
    "order_cancel_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
)

FORCED_FALSE_EXECUTION_FIELDS = (
    *REQUIRED_FALSE_FLAGS,
    "order_submission_available",
    "order_cancel_available",
    "wallet_available",
    "signer_available",
    "signed_payload_available",
    "signed_order_available",
    "live_execution_allowed",
    "live_execution_performed",
    "wallet_enabled",
    "wallet_used",
    "wallet_connection_attempted",
    "wallet_signing_performed",
    "signer_instantiated",
    "signing_attempted",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "order_payload_generated",
    "real_order_submitted",
    "order_submitted",
    "real_order_cancelled",
    "order_cancelled",
    "order_submission_attempted",
    "order_cancellation_attempted",
    "balance_read_attempted",
    "position_read_attempted",
    "fill_read_attempted",
    "pnl_read_attempted",
    "balance_read_enabled",
    "position_read_enabled",
    "fill_read_enabled",
    "pnl_read_enabled",
    "authenticated_endpoint_call_performed",
    "authenticated_request_performed",
    "real_authenticated_get_performed",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "credential_values_read",
    "credentials_values_read",
    "credential_values_serialized",
    "credentials_values_serialized",
    "credential_values_printed",
    "credential_values_stored",
    "credential_values_hashed",
    "credential_values_transformed",
    "environment_values_read",
    "environment_values_serialized",
    "environment_values_printed",
    "environment_values_stored",
    "environment_secrets_read",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "credentials_values_exposed",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
    "telegram_live_order_controls_added",
    "telegram_signing_controls_added",
    "telegram_wallet_controls_added",
    "live_trading_enabled",
)

FORBIDDEN_MODEL_FIELDS = frozenset(
    {
        "private_key",
        "seed_phrase",
        "mnemonic",
        "api_secret",
        "api_secret_value",
        "auth_token",
        "passphrase",
        "passphrase_value",
        "secret",
        "raw_value",
        "value_hash",
        "value_prefix",
        "value_suffix",
        "value_length",
        "masked_value",
        "signature",
        "signed_payload",
        "signed_order",
        "signed_payload_value",
        "signed_order_value",
        "order_id",
        "client_order_id",
        "tx_hash",
        "transaction_hash",
        "fill_id",
        "fill_price",
        "filled_size",
        "execution_status",
        "balance",
        "balances",
        "position",
        "positions",
        "pnl",
        "profit",
        "realized_pnl",
        "unrealized_pnl",
    }
)


@dataclass(frozen=True)
class ExplicitLiveCredentialMarkerRequirement:
    marker_label: str
    marker_group: str
    required_for_redacted_review: bool
    value_read_allowed: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": EXPLICIT_LIVE_CREDENTIAL_MARKER_REQUIREMENT_CONTRACT,
            "task_id": TASK_ID,
            "marker_label": clean_text(self.marker_label),
            "marker_group": clean_text(self.marker_group),
            "required_for_redacted_review": self.required_for_redacted_review is True,
            "value_read_allowed": False,
            "presence_boolean_only": True,
            "generated_at": self.generated_at,
        }
        return value


@dataclass(frozen=True)
class ExplicitLiveCredentialMarkerPresence:
    marker_label: str
    marker_group: str
    present: bool
    required_for_redacted_review: bool
    result_category: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        category = clean_text(self.result_category) or MARKER_CATEGORY_MISSING
        value = {
            "contract_version": EXPLICIT_LIVE_CREDENTIAL_MARKER_PRESENCE_CONTRACT,
            "task_id": TASK_ID,
            "marker_label": clean_text(self.marker_label),
            "marker_group": clean_text(self.marker_group),
            "present": self.present is True,
            "required_for_redacted_review": self.required_for_redacted_review is True,
            "result_category": category,
            "presence_boolean_only": True,
            "value_read": False,
            "value_redacted": True,
            "raw_value_emitted": False,
            "generated_at": self.generated_at,
        }
        return value


@dataclass(frozen=True)
class ExplicitLiveCredentialMarkerPresenceReport:
    market_symbol: str
    strategy_name: str
    marker_requirements: tuple[Mapping[str, Any], ...]
    marker_checks: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        requirements = [dict(row) for row in self.marker_requirements]
        checks = [dict(row) for row in self.marker_checks]
        required_checks = [row for row in checks if row.get("required_for_redacted_review") is True]
        missing_required = [
            clean_text(row.get("marker_label"))
            for row in required_checks
            if row.get("present") is not True
        ]
        present_execution_flags = [
            clean_text(row.get("marker_label"))
            for row in checks
            if row.get("marker_group") == MARKER_GROUP_EXECUTION_FLAG and row.get("present") is True
        ]
        value = {
            "contract_version": EXPLICIT_LIVE_CREDENTIAL_MARKER_PRESENCE_REPORT_CONTRACT,
            "task_id": TASK_ID,
            "market": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "market_symbol": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "strategy_name": clean_text(self.strategy_name) or DEFAULT_ALLOWED_STRATEGY,
            "marker_requirements": requirements,
            "marker_checks": checks,
            "marker_count": len(checks),
            "required_marker_count": len(required_checks),
            "present_marker_count": sum(1 for row in checks if row.get("present") is True),
            "missing_required_marker_count": len(missing_required),
            "missing_required_markers": missing_required,
            "present_execution_flag_count": len(present_execution_flags),
            "present_execution_flags": present_execution_flags,
            "all_required_markers_present": bool(required_checks) and not missing_required,
            "execution_flags_absent": not present_execution_flags,
            "presence_only": True,
            "presence_booleans_only": True,
            "explicit_allowlist_only": True,
            "broad_environment_scan_performed": False,
            "environment_presence_checked": True,
            "environment_values_read": False,
            "environment_values_serialized": False,
            "values_redacted": True,
            "raw_values_emitted": False,
            "readiness_status": STATUS_BLOCKED,
            "operator_summary": (
                "Explicit marker names were checked for presence only. Values were not read, parsed, printed, "
                "stored, hashed, transformed, or serialized."
            ),
            "generated_at": self.generated_at,
        }
        value.update(explicit_live_credentials_readiness_safety_flags())
        return value


@dataclass(frozen=True)
class ExplicitLiveCredentialsOperatorApprovalBoundary:
    market_symbol: str
    strategy_name: str
    operator_review_marker_present: bool
    dual_control_review_marker_present: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": EXPLICIT_LIVE_CREDENTIAL_OPERATOR_APPROVAL_BOUNDARY_CONTRACT,
            "task_id": TASK_ID,
            "market": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "market_symbol": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "strategy_name": clean_text(self.strategy_name) or DEFAULT_ALLOWED_STRATEGY,
            "operator_review_marker_present": self.operator_review_marker_present is True,
            "dual_control_review_marker_present": self.dual_control_review_marker_present is True,
            "operator_approved": False,
            "allowed_for_live": False,
            "operator_review_does_not_enable_live": True,
            "separate_live_enabling_task_required": True,
            "separate_wallet_signing_task_required": True,
            "separate_authenticated_request_task_required": True,
            "separate_order_submission_or_cancel_task_required": True,
            "generated_at": self.generated_at,
        }
        value.update(explicit_live_credentials_readiness_safety_flags())
        return value


@dataclass(frozen=True)
class ExplicitLiveCredentialsSafetyPolicyValidation:
    marker_presence_report: Mapping[str, Any]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        report = dict(self.marker_presence_report)
        checks = [dict(row) for row in report.get("marker_checks", []) if isinstance(row, Mapping)]
        forbidden_fields = sorted({path for path, key, _ in _walk_fields(report) if key in FORBIDDEN_MODEL_FIELDS})
        value = {
            "contract_version": EXPLICIT_LIVE_CREDENTIAL_SAFETY_POLICY_VALIDATION_CONTRACT,
            "task_id": TASK_ID,
            "valid": not forbidden_fields,
            "status": "passed" if not forbidden_fields else STATUS_BLOCKED,
            "presence_check_count": len(checks),
            "forbidden_field_count": len(forbidden_fields),
            "forbidden_field_paths": forbidden_fields,
            "explicit_allowlist_only": report.get("explicit_allowlist_only") is True,
            "presence_booleans_only": report.get("presence_booleans_only") is True,
            "broad_environment_scan_performed": False,
            "credential_values_read": False,
            "credential_values_serialized": False,
            "credential_values_printed": False,
            "credential_values_stored": False,
            "credential_values_hashed": False,
            "credential_values_transformed": False,
            "generated_at": self.generated_at,
        }
        value.update(explicit_live_credentials_readiness_safety_flags())
        return value


@dataclass(frozen=True)
class ExplicitLiveCredentialsReadinessBlocker:
    blocker_id: str
    blocker_category: str
    reason: str
    severity: str = "critical"
    resolution_status: str = "unresolved"
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = EXPLICIT_LIVE_CREDENTIAL_BLOCKER_CONTRACT
        value["task_id"] = TASK_ID
        value["blocker_id"] = clean_text(self.blocker_id)
        value["blocker_category"] = clean_text(self.blocker_category)
        value["reason"] = clean_text(self.reason)
        value["severity"] = clean_text(self.severity) or "critical"
        value["resolution_status"] = "unresolved"
        value["resolved"] = False
        value["blocks_live_execution"] = True
        return value


@dataclass(frozen=True)
class ExplicitLiveCredentialsReadinessBlockerMatrix:
    market_symbol: str
    strategy_name: str
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blockers = [dict(row) for row in self.blockers]
        value = {
            "contract_version": EXPLICIT_LIVE_CREDENTIAL_BLOCKER_MATRIX_CONTRACT,
            "task_id": TASK_ID,
            "market": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "market_symbol": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "strategy_name": clean_text(self.strategy_name) or DEFAULT_ALLOWED_STRATEGY,
            "blockers": blockers,
            "blocker_count": len(blockers),
            "resolved_blocker_count": 0,
            "required_unresolved_blocker_ids": list(REQUIRED_UNRESOLVED_BLOCKER_IDS),
            "unresolved_blocker_ids": [clean_text(row.get("blocker_id")) for row in blockers],
            "generated_at": self.generated_at,
        }
        value.update(explicit_live_credentials_readiness_safety_flags())
        return value


@dataclass(frozen=True)
class ExplicitLiveCredentialsOperatorChecklist:
    market_symbol: str
    strategy_name: str
    marker_presence_report: Mapping[str, Any]
    operator_approval_boundary: Mapping[str, Any]
    safety_policy_validation: Mapping[str, Any]
    blocker_matrix: Mapping[str, Any]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        checklist_items = _checklist_items(
            marker_presence_report=dict(self.marker_presence_report),
            operator_approval_boundary=dict(self.operator_approval_boundary),
            safety_policy_validation=dict(self.safety_policy_validation),
            blocker_matrix=dict(self.blocker_matrix),
        )
        value = {
            "contract_version": EXPLICIT_LIVE_CREDENTIAL_OPERATOR_CHECKLIST_CONTRACT,
            "task_id": TASK_ID,
            "market": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "market_symbol": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "strategy_name": clean_text(self.strategy_name) or DEFAULT_ALLOWED_STRATEGY,
            "checklist_items": checklist_items,
            "ready_item_count": sum(1 for row in checklist_items if row.get("ready") is True),
            "blocked_item_count": sum(1 for row in checklist_items if row.get("ready") is not True),
            "operator_approved": False,
            "candidate_is_executable": False,
            "allowed_for_live": False,
            "resolved_blocker_count": 0,
            "next_operator_action": "review redacted presence artifacts; use a separate future task for any live enablement",
            "generated_at": self.generated_at,
        }
        value.update(explicit_live_credentials_readiness_safety_flags())
        return value


@dataclass(frozen=True)
class ExplicitLiveCredentialsReadinessSummary:
    market_symbol: str
    strategy_name: str
    marker_presence_path: str
    operator_approval_boundary_path: str
    safety_policy_validation_path: str
    blocker_matrix_path: str
    marker_presence_report: Mapping[str, Any]
    operator_approval_boundary: Mapping[str, Any]
    safety_policy_validation: Mapping[str, Any]
    blocker_matrix: Mapping[str, Any]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        marker_report = dict(self.marker_presence_report)
        blocker_matrix = dict(self.blocker_matrix)
        safety_policy = dict(self.safety_policy_validation)
        redacted_review_ready = (
            marker_report.get("all_required_markers_present") is True
            and marker_report.get("execution_flags_absent") is True
            and safety_policy.get("valid") is True
        )
        readiness_status = (
            STATUS_REDACTED_PRESENCE_REVIEW_READY if redacted_review_ready else STATUS_BLOCKED
        )
        value = {
            "contract_version": EXPLICIT_LIVE_CREDENTIALS_READINESS_SUMMARY_CONTRACT,
            "task_id": TASK_ID,
            "design_reference": DESIGN_REFERENCE_TASK_ID,
            "market": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "market_symbol": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "strategy_name": clean_text(self.strategy_name) or DEFAULT_ALLOWED_STRATEGY,
            "readiness_status": readiness_status,
            "redacted_presence_review_ready": redacted_review_ready,
            "live_ready": False,
            "allowed_for_live": False,
            "marker_presence_path": clean_text(self.marker_presence_path),
            "operator_approval_boundary_path": clean_text(self.operator_approval_boundary_path),
            "safety_policy_validation_path": clean_text(self.safety_policy_validation_path),
            "blocker_matrix_path": clean_text(self.blocker_matrix_path),
            "required_marker_count": int(marker_report.get("required_marker_count", 0) or 0),
            "missing_required_marker_count": int(marker_report.get("missing_required_marker_count", 0) or 0),
            "present_execution_flag_count": int(marker_report.get("present_execution_flag_count", 0) or 0),
            "blocker_count": int(blocker_matrix.get("blocker_count", 0) or 0),
            "resolved_blocker_count": 0,
            "operator_summary": (
                "Credential marker coverage is review-only. Even a redacted review-ready result does not approve "
                "live execution or resolve live blockers."
            ),
            "generated_at": self.generated_at,
        }
        value.update(explicit_live_credentials_readiness_safety_flags())
        return value


@dataclass(frozen=True)
class ExplicitLiveCredentialsReadinessGate:
    status: str
    market_symbol: str
    strategy_name: str
    marker_presence_report: Mapping[str, Any]
    operator_approval_boundary: Mapping[str, Any]
    safety_policy_validation: Mapping[str, Any]
    blocker_matrix: Mapping[str, Any]
    operator_checklist: Mapping[str, Any]
    readiness_summary: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blocker_matrix = dict(self.blocker_matrix)
        blockers = [dict(row) for row in blocker_matrix.get("blockers", []) if isinstance(row, Mapping)]
        value = {
            "contract_version": EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_CONTRACT,
            "task_id": TASK_ID,
            "design_reference": DESIGN_REFERENCE_TASK_ID,
            "status": clean_text(self.status),
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "review_only": True,
            "preflight_only": True,
            "preparation_only": True,
            "gate_only": True,
            "dry_run": True,
            "market": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "market_symbol": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "strategy_name": clean_text(self.strategy_name) or DEFAULT_ALLOWED_STRATEGY,
            "operator_approved": False,
            "candidate_is_executable": False,
            "allowed_for_live": False,
            "live_ready": False,
            "blocker_count": len(blockers),
            "resolved_blocker_count": 0,
            "blockers": blockers,
            "marker_presence_report": dict(self.marker_presence_report),
            "operator_approval_boundary": dict(self.operator_approval_boundary),
            "safety_policy_validation": dict(self.safety_policy_validation),
            "blocker_matrix": blocker_matrix,
            "operator_checklist": dict(self.operator_checklist),
            "readiness_summary": dict(self.readiness_summary),
            "latest_status": dict(self.latest_status),
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": (
                "Explicit live credentials readiness gate generated redacted presence-only artifacts. It does not "
                "read credential values, connect a wallet, sign, submit, cancel, or make authenticated calls."
            ),
            "generated_at": self.generated_at,
        }
        value.update(explicit_live_credentials_readiness_safety_flags())
        value["validation"] = validate_explicit_live_credentials_readiness_gate(value, generated_at=self.generated_at)
        return value


def explicit_live_credentials_readiness_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "preflight_only": True,
        "preparation_only": True,
        "gate_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "presence_only": True,
        "presence_booleans_only": True,
        "explicit_allowlist_only": True,
        "broad_environment_scan_performed": False,
        "environment_values_read": False,
        "environment_values_serialized": False,
        "environment_values_printed": False,
        "environment_values_stored": False,
        "credential_values_read": False,
        "credentials_values_read": False,
        "credential_values_serialized": False,
        "credentials_values_serialized": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "credential_values_hashed": False,
        "credential_values_transformed": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "operator_approved": False,
        "candidate_is_executable": False,
        "order_submission_available": False,
        "order_cancel_available": False,
        "wallet_available": False,
        "signer_available": False,
        "signed_payload_available": False,
        "signed_order_available": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_connection_attempted": False,
        "wallet_signing_performed": False,
        "signer_instantiated": False,
        "signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signed_payload_generated": False,
        "signed_order_payload_generated": False,
        "order_payload_generated": False,
        "real_order_submitted": False,
        "order_submitted": False,
        "real_order_cancelled": False,
        "order_cancelled": False,
        "order_submission_attempted": False,
        "order_cancellation_attempted": False,
        "balance_read_attempted": False,
        "position_read_attempted": False,
        "fill_read_attempted": False,
        "pnl_read_attempted": False,
        "balance_read_enabled": False,
        "position_read_enabled": False,
        "fill_read_enabled": False,
        "pnl_read_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "real_authenticated_get_performed": False,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "credentials_values_exposed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "telegram_live_order_controls_added": False,
        "telegram_signing_controls_added": False,
        "telegram_wallet_controls_added": False,
        "live_trading_enabled": False,
        "resolved_blocker_count": 0,
    }


def validate_explicit_live_credentials_readiness_gate(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_CONTRACT:
        errors.append(f"contract_version must be {EXPLICIT_LIVE_CREDENTIALS_READINESS_GATE_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append("execution_mode must be preflight")
        statuses.append("invalid_execution_mode")
    for field in (
        "review_only",
        "preflight_only",
        "preparation_only",
        "gate_only",
        "non_executable",
        "presence_only",
        "presence_booleans_only",
    ):
        if value.get(field) is not True:
            errors.append(f"{field} must be true")
            statuses.append(f"{field}_missing")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
        statuses.append("resolved_blocker_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    blocker_ids = {
        clean_text(row.get("blocker_id")) for row in value.get("blockers", []) if isinstance(row, Mapping)
    }
    for blocker_id in REQUIRED_UNRESOLVED_BLOCKER_IDS:
        if blocker_id not in blocker_ids:
            errors.append(f"required unresolved blocker missing: {blocker_id}")
            statuses.append("required_blocker_missing")
    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must remain 0")
            statuses.append("nested_resolved_blocker_detected")
        if key in FORBIDDEN_MODEL_FIELDS:
            errors.append(f"{path}.{key} is forbidden in explicit live credentials readiness artifacts")
            statuses.append("forbidden_model_field_detected")
    valid = not errors
    return {
        "contract_version": EXPLICIT_LIVE_CREDENTIALS_READINESS_VALIDATION_CONTRACT,
        "validation_id": "explicit-live-credentials-readiness-validation-064-passed"
        if valid
        else "explicit-live-credentials-readiness-validation-064-blocked",
        "valid": valid,
        "status": "passed" if valid else STATUS_BLOCKED,
        "statuses": _dedupe(statuses)
        or (["explicit_live_credentials_readiness_gate_valid"] if valid else ["explicit_live_credentials_readiness_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **explicit_live_credentials_readiness_safety_flags(),
    }


def _checklist_items(
    *,
    marker_presence_report: Mapping[str, Any],
    operator_approval_boundary: Mapping[str, Any],
    safety_policy_validation: Mapping[str, Any],
    blocker_matrix: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        _item("explicit_marker_allowlist_used", True, "only explicit marker labels are checked"),
        _item("presence_booleans_only", True, "only marker presence booleans are recorded"),
        _item("credential_values_not_read", True, "credential values are not read or serialized"),
        _item(
            "required_markers_present",
            int(marker_presence_report.get("missing_required_marker_count", 0) or 0) == 0,
            "missing required markers keep the gate blocked",
        ),
        _item(
            "execution_flags_absent",
            int(marker_presence_report.get("present_execution_flag_count", 0) or 0) == 0,
            "present execution flags are conflicts and do not enable live execution",
        ),
        _item(
            "operator_review_marker_present",
            operator_approval_boundary.get("operator_review_marker_present") is True,
            "operator review marker presence is required for redacted review readiness",
        ),
        _item(
            "dual_control_review_marker_present",
            operator_approval_boundary.get("dual_control_review_marker_present") is True,
            "dual-control marker presence is required for redacted review readiness",
        ),
        _item(
            "safety_policy_valid",
            safety_policy_validation.get("valid") is True,
            "secret-safety policy validation must pass",
        ),
        _item("operator_approved_false", False, "operator_approved remains false"),
        _item("candidate_non_executable", False, "candidate_is_executable remains false"),
        _item(
            "unresolved_blockers_present",
            False,
            f"{int(blocker_matrix.get('blocker_count', 0) or 0)} unresolved blockers remain",
        ),
    ]


def _item(check_id: str, ready: bool, detail: str) -> dict[str, Any]:
    return {
        "check_id": clean_text(check_id),
        "ready": ready is True,
        "status": "ready" if ready is True else STATUS_BLOCKED,
        "detail": clean_text(detail),
    }


def _walk_fields(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            rows.append((path, key_text, nested))
            rows.extend(_walk_fields(nested, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk_fields(nested, f"{path}[{index}]"))
    return rows


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result
