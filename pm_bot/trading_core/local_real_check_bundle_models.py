from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-072C-LOCAL-REAL-CHECK-BUNDLE-NO-LIVE"

MODE = "local real-check bundle / manual one-shot / dry-run / no-live"
EXECUTION_MODE = "local_real_check_bundle_072c"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

CLOB_SUBCHECK_ID = "clob_l2_auth_readonly_probe_067c"
LIVE_ACCOUNT_SUBCHECK_ID = "live_account_readonly_state_probe_070c"
GUARDED_SIGNER_SUBCHECK_ID = "guarded_signer_diagnostic_smoke_069a"
PUBLIC_DISCOVERY_SUBCHECK_ID = "public_market_token_discovery_071a"
DISCOVERY_BRIDGE_SUBCHECK_ID = "discovery_to_token_resolver_bridge_071d"
LIVE_STATUS_SUBCHECK_ID = "live_readonly_status_aggregator_071b"

SUBCHECK_SEQUENCE = (
    CLOB_SUBCHECK_ID,
    LIVE_ACCOUNT_SUBCHECK_ID,
    GUARDED_SIGNER_SUBCHECK_ID,
    PUBLIC_DISCOVERY_SUBCHECK_ID,
    DISCOVERY_BRIDGE_SUBCHECK_ID,
    LIVE_STATUS_SUBCHECK_ID,
)

SUBCHECK_LABELS = {
    CLOB_SUBCHECK_ID: "CLOB L2 auth read-only probe",
    LIVE_ACCOUNT_SUBCHECK_ID: "Live account read-only state probe",
    GUARDED_SIGNER_SUBCHECK_ID: "Guarded signer diagnostic smoke",
    PUBLIC_DISCOVERY_SUBCHECK_ID: "Public market token discovery",
    DISCOVERY_BRIDGE_SUBCHECK_ID: "Discovery-to-token resolver bridge",
    LIVE_STATUS_SUBCHECK_ID: "Live read-only status aggregator",
}

STATUS_COMPLETED_WITH_FAILED_SUBCHECKS = "local_real_check_bundle_completed_with_failed_subchecks_live_blocked"
STATUS_COMPLETED_WITH_BLOCKERS = "local_real_check_bundle_completed_with_blockers_live_blocked"
STATUS_COMPLETED_REPORTED = "local_real_check_bundle_completed_reported_live_blocked"

BUNDLE_RESULT_CONTRACT = "pmbot_local_real_check_bundle_072c_result.v1"
BUNDLE_LATEST_STATUS_CONTRACT = "pmbot_latest_local_real_check_bundle_status_072c.v1"
BUNDLE_SUBCHECK_CONTRACT = "pmbot_local_real_check_bundle_subcheck_072c.v1"
BUNDLE_SUBCHECKS_CONTRACT = "pmbot_local_real_check_bundle_subchecks_072c.v1"
BUNDLE_BLOCKER_CONTRACT = "pmbot_local_real_check_bundle_blocker_072c.v1"
BUNDLE_BLOCKERS_CONTRACT = "pmbot_local_real_check_bundle_blockers_072c.v1"
BUNDLE_SAFETY_SNAPSHOT_CONTRACT = "pmbot_local_real_check_bundle_safety_snapshot_072c.v1"
BUNDLE_VALIDATION_CONTRACT = "pmbot_local_real_check_bundle_validation_072c.v1"

SUCCESS_STATUSES = frozenset(
    {
        "authenticated_readonly_probe_succeeded_live_blocked",
        "account_state_probe_succeeded_live_blocked",
        "diagnostic_ok",
        "source_backed_candidates_ready",
        "ready_source_backed_token_contract",
        "live_readonly_status_aggregated",
    }
)

BLOCKED_STATUS_PREFIXES = ("blocked",)
BLOCKED_STATUS_FRAGMENTS = ("_blocked", "selection_required", "unavailable", "no_candidates")

FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "bundle_executable_for_live",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "order_submission_enabled",
    "order_submission_attempted",
    "order_submission_performed",
    "order_submitted",
    "real_order_submitted",
    "order_cancellation_enabled",
    "order_cancellation_attempted",
    "order_cancellation_performed",
    "order_cancelled",
    "real_order_cancelled",
    "order_payload_signing_enabled",
    "order_payload_signing_attempted",
    "order_payload_signed",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "signed_order_generated",
    "wallet_connection_enabled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "wallet_signing_performed",
    "signer_instantiated",
    "signing_enabled",
    "signing_attempted",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "authenticated_trading_enabled",
    "authenticated_request_performed",
    "authenticated_trading_call_performed",
    "post_put_patch_delete_attempted",
    "trading_endpoint_write_attempted",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
    "private_key_read",
    "wallet_private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "raw_secret_values_printed",
    "raw_secret_values_persisted",
    "secrets_printed",
    "secrets_persisted",
    "fake_data_generated",
    "fake_success_inferred",
)


def local_real_check_bundle_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "manual_one_shot_only": True,
        "dry_run_only": True,
        "review_only": True,
        "status_capture_only": True,
        "no_fake_data": True,
        "no_fake_success": True,
        "allowed_for_live": False,
        "bundle_executable_for_live": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_performed": False,
        "order_submitted": False,
        "real_order_submitted": False,
        "order_cancellation_enabled": False,
        "order_cancellation_attempted": False,
        "order_cancellation_performed": False,
        "order_cancelled": False,
        "real_order_cancelled": False,
        "order_payload_signing_enabled": False,
        "order_payload_signing_attempted": False,
        "order_payload_signed": False,
        "signed_payload_generated": False,
        "signed_order_payload_generated": False,
        "signed_order_generation_enabled": False,
        "signed_order_generation_attempted": False,
        "signed_order_generated": False,
        "wallet_connection_enabled": False,
        "wallet_connection_attempted": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_attempted": False,
        "wallet_signing_performed": False,
        "signer_instantiated": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "authenticated_trading_enabled": False,
        "authenticated_request_performed": False,
        "authenticated_trading_call_performed": False,
        "post_put_patch_delete_attempted": False,
        "trading_endpoint_write_attempted": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "private_key_read": False,
        "wallet_private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "raw_secret_values_printed": False,
        "raw_secret_values_persisted": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "fake_data_generated": False,
        "fake_success_inferred": False,
        "resolved_blocker_count": 0,
    }


@dataclass(frozen=True)
class LocalRealCheckBundleSubcheckStatus:
    subcheck_id: str
    subcheck_label: str
    sequence_index: int
    status: str
    classification: str
    completed: bool
    failed: bool
    exception_type: str = ""
    error_message_sanitized: str = ""
    artifact_path: str = ""
    latest_status_path: str = ""
    blocker_count: int = 0
    source_blocker_count: int = 0
    status_fields: Mapping[str, Any] | None = None
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = BUNDLE_SUBCHECK_CONTRACT
        value["task_id"] = TASK_ID
        value["subcheck_id"] = clean_text(self.subcheck_id)
        value["subcheck_label"] = clean_text(self.subcheck_label)
        value["status"] = clean_text(self.status) or "unknown"
        value["classification"] = clean_text(self.classification) or "unknown"
        value["completed"] = self.completed is True
        value["failed"] = self.failed is True
        value["exception_type"] = clean_text(self.exception_type)
        value["error_message_sanitized"] = clean_text(self.error_message_sanitized)
        value["artifact_path"] = clean_text(self.artifact_path)
        value["latest_status_path"] = clean_text(self.latest_status_path)
        value["blocker_count"] = int(self.blocker_count or 0)
        value["source_blocker_count"] = int(self.source_blocker_count or 0)
        value["status_fields"] = dict(self.status_fields or {})
        value["raw_subcheck_payload_embedded"] = False
        value["safe_for_artifacts"] = True
        value.update(local_real_check_bundle_safety_flags())
        return value


@dataclass(frozen=True)
class LocalRealCheckBundleBlocker:
    blocker_id: str
    blocker_category: str
    reason: str
    subcheck_id: str = ""
    source_status: str = ""
    source_blocker_id: str = ""
    severity: str = "critical"
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": BUNDLE_BLOCKER_CONTRACT,
            "task_id": TASK_ID,
            "blocker_id": clean_text(self.blocker_id),
            "blocker_category": clean_text(self.blocker_category),
            "severity": clean_text(self.severity) or "critical",
            "reason": clean_text(self.reason),
            "subcheck_id": clean_text(self.subcheck_id),
            "source_status": clean_text(self.source_status),
            "source_blocker_id": clean_text(self.source_blocker_id),
            "resolution_status": "unresolved",
            "resolved": False,
            "blocks_live_execution": True,
            "generated_at": self.generated_at,
        }
        value.update(local_real_check_bundle_safety_flags())
        return value


@dataclass(frozen=True)
class LocalRealCheckBundleLatestStatus:
    market: str
    strategy: str
    status: str
    subchecks: Sequence[Mapping[str, Any]]
    blocker_count: int
    artifact_paths: Mapping[str, str]
    private_key_diagnostic_requested: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        rows = [dict(row) for row in self.subchecks]
        artifact_paths = dict(self.artifact_paths)
        value = {
            "contract_version": BUNDLE_LATEST_STATUS_CONTRACT,
            "task_id": TASK_ID,
            "market": clean_text(self.market).upper() or DEFAULT_MARKET,
            "strategy": clean_text(self.strategy) or DEFAULT_STRATEGY,
            "status": clean_text(self.status),
            "subcheck_count": len(rows),
            "subcheck_completed_count": sum(1 for row in rows if row.get("completed") is True),
            "subcheck_failed_count": sum(1 for row in rows if row.get("failed") is True),
            "subcheck_blocked_count": sum(1 for row in rows if row.get("classification") == "blocked"),
            "all_subchecks_completed": all(row.get("completed") is True for row in rows),
            "all_subchecks_reported_success": all(row.get("classification") == "reported_success" for row in rows),
            "blocker_count": int(self.blocker_count or 0),
            "resolved_blocker_count": 0,
            "private_key_diagnostic_requested": self.private_key_diagnostic_requested is True,
            "subcheck_statuses": {
                clean_text(row.get("subcheck_id")): clean_text(row.get("status")) for row in rows
            },
            "artifact_path": clean_text(artifact_paths.get("result")),
            "latest_status_path": clean_text(artifact_paths.get("latest_status")),
            "subchecks_path": clean_text(artifact_paths.get("subchecks")),
            "blockers_path": clean_text(artifact_paths.get("blockers")),
            "safety_snapshot_path": clean_text(artifact_paths.get("safety_snapshot")),
            "operator_summary_path": clean_text(artifact_paths.get("operator_summary")),
            "generated_at": self.generated_at,
        }
        value.update(local_real_check_bundle_safety_flags())
        return value


@dataclass(frozen=True)
class LocalRealCheckBundleResult:
    market: str
    strategy: str
    status: str
    subchecks: Sequence[Mapping[str, Any]]
    blockers: Sequence[Mapping[str, Any]]
    latest_status: Mapping[str, Any]
    safety_snapshot: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    operator_summary: str
    private_key_diagnostic_requested: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        subchecks = [dict(row) for row in self.subchecks]
        blockers = [dict(row) for row in self.blockers]
        latest = dict(self.latest_status)
        value = {
            "contract_version": BUNDLE_RESULT_CONTRACT,
            "task_id": TASK_ID,
            "market": clean_text(self.market).upper() or DEFAULT_MARKET,
            "strategy": clean_text(self.strategy) or DEFAULT_STRATEGY,
            "status": clean_text(self.status),
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "dry_run": True,
            "manual_one_shot_only": True,
            "private_key_diagnostic_requested": self.private_key_diagnostic_requested is True,
            "subchecks": subchecks,
            "subcheck_count": len(subchecks),
            "subcheck_completed_count": sum(1 for row in subchecks if row.get("completed") is True),
            "subcheck_failed_count": sum(1 for row in subchecks if row.get("failed") is True),
            "subcheck_blocked_count": sum(1 for row in subchecks if row.get("classification") == "blocked"),
            "all_subchecks_completed": all(row.get("completed") is True for row in subchecks),
            "all_subchecks_reported_success": all(
                row.get("classification") == "reported_success" for row in subchecks
            ),
            "blockers": blockers,
            "blocker_count": len(blockers),
            "resolved_blocker_count": 0,
            "latest_status": latest,
            "safety_snapshot": dict(self.safety_snapshot),
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": clean_text(self.operator_summary),
            "generated_at": self.generated_at,
        }
        value.update(local_real_check_bundle_safety_flags())
        value["validation"] = validate_local_real_check_bundle_result(value, generated_at=self.generated_at)
        return value


def build_safety_snapshot(
    *,
    market: str,
    strategy: str,
    private_key_diagnostic_requested: bool,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = {
        "contract_version": BUNDLE_SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "status": "local_real_check_bundle_safety_active",
        "market": clean_text(market).upper() or DEFAULT_MARKET,
        "strategy": clean_text(strategy) or DEFAULT_STRATEGY,
        "manual_one_shot_only": True,
        "private_key_diagnostic_requires_explicit_flag": True,
        "private_key_diagnostic_requested": private_key_diagnostic_requested is True,
        "private_key_diagnostic_passed_only_to_guarded_signer_subcheck": True,
        "status_capture_only": True,
        "raw_subcheck_payloads_embedded": False,
        "forbidden_actions": [
            "order submission",
            "order cancellation",
            "order payload signing",
            "trading write endpoint calls",
            "live trading enablement",
            "secret output",
            "browser automation",
            "scheduler, daemon, or background loop",
        ],
        "generated_at": generated_at,
    }
    value.update(local_real_check_bundle_safety_flags())
    return value


def build_subchecks_artifact(
    subchecks: Sequence[Mapping[str, Any]],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    rows = [dict(row) for row in subchecks]
    value = {
        "contract_version": BUNDLE_SUBCHECKS_CONTRACT,
        "task_id": TASK_ID,
        "status": "local_real_check_bundle_subchecks_recorded",
        "subcheck_sequence": list(SUBCHECK_SEQUENCE),
        "subcheck_count": len(rows),
        "subchecks": rows,
        "generated_at": generated_at,
    }
    value.update(local_real_check_bundle_safety_flags())
    return value


def build_blockers_artifact(
    blockers: Sequence[Mapping[str, Any]],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    rows = [dict(row) for row in blockers]
    value = {
        "contract_version": BUNDLE_BLOCKERS_CONTRACT,
        "task_id": TASK_ID,
        "status": "local_real_check_bundle_blockers_recorded",
        "blocker_count": len(rows),
        "resolved_blocker_count": 0,
        "blockers": rows,
        "generated_at": generated_at,
    }
    value.update(local_real_check_bundle_safety_flags())
    return value


def classify_subcheck_status(status: str, *, failed: bool) -> str:
    normalized = clean_text(status)
    lowered = normalized.lower()
    if failed:
        return "failed"
    if normalized in SUCCESS_STATUSES:
        return "reported_success"
    if lowered.startswith(BLOCKED_STATUS_PREFIXES) or any(fragment in lowered for fragment in BLOCKED_STATUS_FRAGMENTS):
        return "blocked"
    if normalized:
        return "reported_status"
    return "unknown"


def bundle_status_from_subchecks(
    subchecks: Sequence[Mapping[str, Any]],
    blockers: Sequence[Mapping[str, Any]],
) -> str:
    if any(row.get("failed") is True for row in subchecks):
        return STATUS_COMPLETED_WITH_FAILED_SUBCHECKS
    if blockers:
        return STATUS_COMPLETED_WITH_BLOCKERS
    return STATUS_COMPLETED_REPORTED


def validate_local_real_check_bundle_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != BUNDLE_RESULT_CONTRACT:
        errors.append(f"contract_version must be {BUNDLE_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append("execution_mode must match local_real_check_bundle_072c")
        statuses.append("invalid_execution_mode")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    if value.get("manual_one_shot_only") is not True:
        errors.append("manual_one_shot_only must be true")
        statuses.append("manual_one_shot_missing")
    subchecks = [row for row in value.get("subchecks", []) if isinstance(row, Mapping)]
    if [clean_text(row.get("subcheck_id")) for row in subchecks] != list(SUBCHECK_SEQUENCE):
        errors.append("subchecks must preserve the required ordered safe real-check sequence")
        statuses.append("subcheck_sequence_invalid")
    if value.get("allowed_for_live") is not False:
        errors.append("allowed_for_live must be false")
        statuses.append("allowed_for_live_not_false")
    if value.get("bundle_executable_for_live") is not False:
        errors.append("bundle_executable_for_live must be false")
        statuses.append("bundle_executable_for_live_not_false")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must remain 0")
        statuses.append("resolved_blocker_detected")
    if any(row.get("failed") is True for row in subchecks):
        if value.get("status") == STATUS_COMPLETED_REPORTED:
            errors.append("bundle cannot report clean completion when any subcheck failed")
            statuses.append("fake_success_detected")
        if value.get("all_subchecks_reported_success") is True:
            errors.append("all_subchecks_reported_success cannot be true when a subcheck failed")
            statuses.append("fake_success_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        expected = 0 if field == "resolved_blocker_count" else False
        if value.get(field) != expected:
            errors.append(f"{field} must be {expected!r}")
            statuses.append("unsafe_execution_flag_detected")
    valid = not errors
    return {
        "contract_version": BUNDLE_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "local-real-check-bundle-validation-072c",
            {"status": value.get("status"), "errors": errors},
        ),
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses)
        or (["local_real_check_bundle_valid"] if valid else ["local_real_check_bundle_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **local_real_check_bundle_safety_flags(),
    }


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
