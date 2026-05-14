from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-SAFETY-060Q-STATIC-SAFETY-INVARIANT-REPORT"

STATIC_SAFETY_INVARIANT_CONFIG_CONTRACT = "pmbot_static_safety_invariant_report_config_060q.v1"
STATIC_SAFETY_INVARIANT_FINDING_CONTRACT = "pmbot_static_safety_invariant_finding_060q.v1"
STATIC_SAFETY_INVARIANT_REPORT_CONTRACT = "pmbot_static_safety_invariant_report_060q.v1"
STATIC_SAFETY_INVARIANT_LATEST_STATUS_CONTRACT = "pmbot_static_safety_invariant_latest_status_060q.v1"
STATIC_SAFETY_INVARIANT_ALLOWLIST_CONTRACT = "pmbot_static_safety_invariant_allowlist_060q.v1"

SEVERITY_CRITICAL = "critical"
SEVERITY_WARNING = "warning"
SEVERITY_ALLOWED_REFERENCE = "allowed_reference"
SEVERITIES = (SEVERITY_CRITICAL, SEVERITY_WARNING, SEVERITY_ALLOWED_REFERENCE)

SCAN_MODE = "static / review-only"
EXECUTION_MODE = "preflight"

SAFE_FALSE_FLAGS = (
    "live_execution_approved",
    "order_submission_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
    "resolved_blocker_count",
)

FORCED_FALSE_EXECUTION_FIELDS = (
    "live_execution_approved",
    "order_submission_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
    "private_key_read",
    "wallet_connection_attempted",
    "signing_attempted",
    "signed_payload_generated",
    "order_submission_attempted",
    "order_cancellation_attempted",
    "balance_read_attempted",
    "position_read_attempted",
    "real_authenticated_get_performed",
    "real_order_submitted",
    "order_submitted",
    "real_order_cancelled",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)

UNSAFE_TRUE_FIELDS = (
    "live_execution_approved",
    "order_submission_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
    "private_key_read",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "wallet_spend_enabled",
    "signing_attempted",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "hmac_signature_generated",
    "auth_signature_generated",
    "order_submission_attempted",
    "order_submission_performed",
    "order_submitted",
    "real_order_submitted",
    "order_cancellation_attempted",
    "order_cancellation_enabled",
    "real_order_cancelled",
    "balance_read_attempted",
    "balance_read_enabled",
    "position_read_attempted",
    "position_read_enabled",
    "authenticated_request_performed",
    "real_authenticated_get_performed",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
    "autonomous_trading_enabled",
    "scheduler_created",
    "daemon_created",
    "background_worker_created",
)

SENSITIVE_NAME_TERMS = (
    "private_key",
    "privatekey",
    "api_secret",
    "api_secret_key",
    "secret_key",
    "passphrase",
    "mnemonic",
    "seed_phrase",
)

EXECUTION_ARTIFACT_FIELDS = (
    "tx",
    "tx_hash",
    "transaction",
    "transaction_hash",
    "order_id",
    "order_hash",
    "signed_order",
    "signed_payload",
    "fill",
    "fill_id",
    "fills",
    "balance",
    "balances",
    "position",
    "positions",
    "pnl",
    "realized_pnl",
    "unrealized_pnl",
)


def static_safety_invariant_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": SCAN_MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "non_executable": True,
        "repo_worktree_only": True,
        "environment_variables_read": False,
        "user_home_directories_read": False,
        "wallet_files_read": False,
        "browser_wallets_inspected": False,
        "network_access_performed": False,
        "real_secrets_handled": False,
        "credential_values_printed": False,
        "credential_values_hashed": False,
        "credential_values_stored": False,
        "credential_values_transformed": False,
        "live_execution_approved": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
    }


@dataclass(frozen=True)
class StaticSafetyInvariantReportConfig:
    scope: str
    dry_run: bool
    include_artifacts: bool
    strict: bool
    artifact_dir: str
    repository_root: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = STATIC_SAFETY_INVARIANT_CONFIG_CONTRACT
        value["task_id"] = TASK_ID
        value["mode"] = SCAN_MODE
        value["execution_mode"] = EXECUTION_MODE
        value["dry_run"] = self.dry_run is True
        value["include_artifacts"] = self.include_artifacts is True
        value["strict"] = self.strict is True
        value["scan_docs_tests"] = self.strict is True
        value.update(static_safety_invariant_safety_flags())
        return value


@dataclass(frozen=True)
class StaticSafetyInvariantFinding:
    finding_id: str
    severity: str
    category: str
    pattern_id: str
    path: str
    line: int
    json_path: str
    detail: str
    evidence: str = "line content redacted"
    allowlist_reason: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        severity = clean_text(self.severity)
        value = asdict(self)
        value["contract_version"] = STATIC_SAFETY_INVARIANT_FINDING_CONTRACT
        value["task_id"] = TASK_ID
        value["severity"] = severity if severity in SEVERITIES else SEVERITY_WARNING
        value["category"] = clean_text(self.category)
        value["pattern_id"] = clean_text(self.pattern_id)
        value["path"] = clean_text(self.path)
        value["line"] = int(self.line or 0)
        value["json_path"] = clean_text(self.json_path)
        value["detail"] = clean_text(self.detail)
        value["evidence"] = clean_text(self.evidence) or "line content redacted"
        value["raw_value_emitted"] = False
        value["credential_value_emitted"] = False
        return value


def severity_counts(findings: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = {severity: 0 for severity in SEVERITIES}
    for finding in findings:
        severity = clean_text(finding.get("severity"))
        if severity in counts:
            counts[severity] += 1
    return counts
