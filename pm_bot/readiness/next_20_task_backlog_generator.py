from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


TASK_ID = "PMBOT-ROADMAP-003-NEXT-20-TASK-BACKLOG-GENERATOR"
CONTRACT_VERSION = "pmbot_next_20_task_backlog.v1"
RUN_MODE = "local_static_next_20_task_backlog_generator"
BACKLOG_ID = "pmbot_next_20_task_backlog_001"
BACKLOG_NAME = "pmbot-next-20-task-backlog"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
CREATED_AT = "2026-05-09T00:00:00Z"

ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/readiness/", "pm_bot/tests/", "tests/")

REQUIRED_VALIDATION_COMMANDS = (
    "python -m compileall pm_bot tests",
    "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
)

SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "network_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}

SOURCE_ARTIFACTS = (
    {
        "artifact_id": "queue_template_task_source",
        "local_reference": "tests/test_codex_queue_pmbot_templates.py",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_role": "fixed_task_id_source",
        "record_state": "local_test_reference",
    },
    {
        "artifact_id": "roadmap_gap_matrix",
        "local_reference": "pm_bot/readiness/PMBOT_ROADMAP_002_PMBOT_LOCAL_TO_SUPERVISED_LIVE_GAP_MATRIX.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_role": "readiness_gap_reference",
        "record_state": "local_readiness_document",
    },
    {
        "artifact_id": "real_wallet_blocker_matrix",
        "local_reference": "pm_bot/readiness/PMBOT_ROADMAP_001_REAL_WALLET_READINESS_BLOCKER_MATRIX.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_role": "sensitive_boundary_reference",
        "record_state": "local_readiness_document",
    },
    {
        "artifact_id": "forbidden_action_boundary",
        "local_reference": "docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_role": "closed_boundary_reference",
        "record_state": "local_safety_document",
    },
)

NEXT_TWENTY_TASK_RECORDS = (
    {
        "artifact_family": "source_ledger",
        "local_reference": "docs/PMBOT_SOURCE_LEDGER_003_SOURCE_QUALITY_REPORT_SUMMARY_LOCAL_ONLY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 1,
        "review_note": "Summarize local source quality rows for human review.",
        "task_id": "PMBOT-SOURCE-LEDGER-003-SOURCE-QUALITY-REPORT-SUMMARY-LOCAL-ONLY",
        "workstream": "source_ledger",
    },
    {
        "artifact_family": "source_ledger",
        "local_reference": "docs/PMBOT_SOURCE_LEDGER_004_SOURCE_QUALITY_REGRESSION_FIXTURE_LOCAL_ONLY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 2,
        "review_note": "Keep a fixed source quality regression fixture for human review.",
        "task_id": "PMBOT-SOURCE-LEDGER-004-SOURCE-QUALITY-REGRESSION-FIXTURE-LOCAL-ONLY",
        "workstream": "source_ledger",
    },
    {
        "artifact_family": "paperlive_decision",
        "local_reference": "docs/PMBOT_PAPERLIVE_DECISION_003_SIMULATED_DECISION_AUDIT_LEDGER_NO_RECOMMENDATIONS.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 3,
        "review_note": "Record simulated decision audit rows with human review pending.",
        "task_id": "PMBOT-PAPERLIVE-DECISION-003-SIMULATED-DECISION-AUDIT-LEDGER-NO-RECOMMENDATIONS",
        "workstream": "paperlive_decision",
    },
    {
        "artifact_family": "paperlive_decision",
        "local_reference": "docs/PMBOT_PAPERLIVE_DECISION_004_SIMULATED_DECISION_REPLAY_SUMMARY_NO_RECOMMENDATIONS.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 4,
        "review_note": "Record simulated decision replay rows with human review pending.",
        "task_id": "PMBOT-PAPERLIVE-DECISION-004-SIMULATED-DECISION-REPLAY-SUMMARY-NO-RECOMMENDATIONS",
        "workstream": "paperlive_decision",
    },
    {
        "artifact_family": "paper_accounting",
        "local_reference": "docs/PMBOT_PAPER_ACCOUNTING_002_PAPER_ONLY_ACCOUNTING_VALIDATOR_LOCAL_ONLY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 5,
        "review_note": "Validate paper-only accounting rows for human review.",
        "task_id": "PMBOT-PAPER-ACCOUNTING-002-PAPER-ONLY-ACCOUNTING-VALIDATOR-LOCAL-ONLY",
        "workstream": "paper_accounting",
    },
    {
        "artifact_family": "paper_accounting",
        "local_reference": "docs/PMBOT_PAPER_ACCOUNTING_003_PAPER_ONLY_SESSION_SUMMARY_LOCAL_ONLY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 6,
        "review_note": "Summarize paper-only session rows for human review.",
        "task_id": "PMBOT-PAPER-ACCOUNTING-003-PAPER-ONLY-SESSION-SUMMARY-LOCAL-ONLY",
        "workstream": "paper_accounting",
    },
    {
        "artifact_family": "crypto_pilot",
        "local_reference": "docs/PMBOT_CRYPTO_PILOT_001_CRYPTO_MARKET_CLASS_CAPTURE_TEMPLATE_LOCAL_ONLY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 7,
        "review_note": "Capture crypto market class fields as static records.",
        "task_id": "PMBOT-CRYPTO-PILOT-001-CRYPTO-MARKET-CLASS-CAPTURE-TEMPLATE-LOCAL-ONLY",
        "workstream": "crypto_pilot",
    },
    {
        "artifact_family": "crypto_pilot",
        "local_reference": "docs/PMBOT_CRYPTO_PILOT_002_CRYPTO_OPERATOR_REVIEW_PROTOCOL_LOCAL_ONLY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 8,
        "review_note": "Document crypto operator review protocol as static records.",
        "task_id": "PMBOT-CRYPTO-PILOT-002-CRYPTO-OPERATOR-REVIEW-PROTOCOL-LOCAL-ONLY",
        "workstream": "crypto_pilot",
    },
    {
        "artifact_family": "crypto_pilot",
        "local_reference": "docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 9,
        "review_note": "Record crypto paperlive observation rows as static records.",
        "task_id": "PMBOT-CRYPTO-PILOT-003-CRYPTO-PAPERLIVE-OBSERVATION-LEDGER-LOCAL-ONLY",
        "workstream": "crypto_pilot",
    },
    {
        "artifact_family": "crypto_pilot",
        "local_reference": "docs/PMBOT_CRYPTO_PILOT_004_CRYPTO_SOURCE_QUALITY_CAPTURE_SURFACE_LOCAL_ONLY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 10,
        "review_note": "Capture crypto source quality rows as static records.",
        "task_id": "PMBOT-CRYPTO-PILOT-004-CRYPTO-SOURCE-QUALITY-CAPTURE-SURFACE-LOCAL-ONLY",
        "workstream": "crypto_pilot",
    },
    {
        "artifact_family": "dashboard",
        "local_reference": "docs/PMBOT_DASHBOARD_002_QUEUE_AND_PAPERLIVE_STATUS_SURFACE.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 11,
        "review_note": "Summarize local queue and paperlive states for human review.",
        "task_id": "PMBOT-DASHBOARD-002-QUEUE-AND-PAPERLIVE-STATUS-SURFACE",
        "workstream": "dashboard",
    },
    {
        "artifact_family": "dashboard",
        "local_reference": "docs/PMBOT_DASHBOARD_003_SOURCE_QUALITY_DASHBOARD_SUMMARY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 12,
        "review_note": "Summarize source quality dashboard rows for human review.",
        "task_id": "PMBOT-DASHBOARD-003-SOURCE-QUALITY-DASHBOARD-SUMMARY",
        "workstream": "dashboard",
    },
    {
        "artifact_family": "dashboard",
        "local_reference": "docs/PMBOT_DASHBOARD_004_PAPER_ACCOUNTING_DASHBOARD_SUMMARY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 13,
        "review_note": "Summarize paper accounting dashboard rows for human review.",
        "task_id": "PMBOT-DASHBOARD-004-PAPER-ACCOUNTING-DASHBOARD-SUMMARY",
        "workstream": "dashboard",
    },
    {
        "artifact_family": "safety",
        "local_reference": "docs/PMBOT_SAFETY_001_AUTONOMY_GATE_CHECKLIST_LOCAL_ONLY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 14,
        "review_note": "Record autonomy gates with human review pending.",
        "task_id": "PMBOT-SAFETY-001-AUTONOMY-GATE-CHECKLIST-LOCAL-ONLY",
        "workstream": "safety",
    },
    {
        "artifact_family": "safety",
        "local_reference": "docs/PMBOT_SAFETY_002_NIGHT_BATCH_POSTRUN_AUDIT_SUMMARY_LOCAL_ONLY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 15,
        "review_note": "Summarize night batch postrun records for human review.",
        "task_id": "PMBOT-SAFETY-002-NIGHT-BATCH-POSTRUN-AUDIT-SUMMARY-LOCAL-ONLY",
        "workstream": "safety",
    },
    {
        "artifact_family": "safety",
        "local_reference": "docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 16,
        "review_note": "Record forbidden action scan rows for human review.",
        "task_id": "PMBOT-SAFETY-003-FORBIDDEN-ACTION-SCAN-LOCAL-ONLY",
        "workstream": "safety",
    },
    {
        "artifact_family": "roadmap",
        "local_reference": "pm_bot/readiness/PMBOT_ROADMAP_002_PMBOT_LOCAL_TO_SUPERVISED_LIVE_GAP_MATRIX.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 17,
        "review_note": "Record local-to-supervised-live gaps for human review.",
        "task_id": "PMBOT-ROADMAP-002-PMBOT-LOCAL-TO-SUPERVISED-LIVE-GAP-MATRIX",
        "workstream": "roadmap",
    },
    {
        "artifact_family": "roadmap",
        "local_reference": "pm_bot/readiness/PMBOT_ROADMAP_003_NEXT_20_TASK_BACKLOG_GENERATOR.md",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 18,
        "review_note": "Generate this static backlog artifact for human review.",
        "task_id": TASK_ID,
        "workstream": "roadmap",
    },
    {
        "artifact_family": "operator",
        "local_reference": "tests/test_codex_queue_pmbot_templates.py",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 19,
        "review_note": "Prepare a morning review pack task record for later human review.",
        "task_id": "PMBOT-OPERATOR-001-MORNING-REVIEW-PACK-LOCAL-ONLY",
        "workstream": "operator",
    },
    {
        "artifact_family": "operator",
        "local_reference": "tests/test_codex_queue_pmbot_templates.py",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_index": 20,
        "review_note": "Prepare a night batch acceptance report task record for later human review.",
        "task_id": "PMBOT-OPERATOR-002-NIGHT-BATCH-ACCEPTANCE-REPORT-LOCAL-ONLY",
        "workstream": "operator",
    },
)


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...]


class Next20TaskBacklogValidationError(ValueError):
    pass


def build_next_20_task_backlog() -> dict:
    task_records = [dict(record) for record in NEXT_TWENTY_TASK_RECORDS]
    source_artifacts = [dict(artifact) for artifact in SOURCE_ARTIFACTS]
    local_references = {artifact["local_reference"] for artifact in source_artifacts}
    local_references.update(record["local_reference"] for record in task_records)

    backlog = {
        "backlog_id": BACKLOG_ID,
        "backlog_name": BACKLOG_NAME,
        "contract_version": CONTRACT_VERSION,
        "created_at": CREATED_AT,
        "errors": [],
        "generator": {
            "generator_id": "next_20_task_backlog_generator_001",
            "generator_state": "deterministic_local_artifact_builder",
            "input_mode": "static_local_constants",
        },
        "local_only": True,
        "operator_review": {
            "reviewed_at": None,
            "reviewed_by": None,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "required_validation_commands": list(REQUIRED_VALIDATION_COMMANDS),
        "run_mode": RUN_MODE,
        "safety_boundaries": dict(SAFETY_BOUNDARIES),
        "source_artifacts": source_artifacts,
        "summary_counts": {
            "local_references": len(local_references),
            "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
            "source_artifacts": len(source_artifacts),
            "task_records": len(task_records),
            "task_records_pending_operator_review": sum(
                1 for record in task_records if record["operator_review_status"] == OPERATOR_REVIEW_STATUS
            ),
            "warnings": 0,
        },
        "task_id": TASK_ID,
        "task_records": task_records,
        "warnings": [],
    }

    validation = validate_next_20_task_backlog(backlog)
    if not validation.valid:
        raise Next20TaskBacklogValidationError("; ".join(validation.errors))
    return backlog


def validate_next_20_task_backlog(backlog: dict) -> ValidationResult:
    errors: list[str] = []

    expected_top_keys = tuple(sorted(_expected_backlog_keys()))
    if tuple(backlog.keys()) != expected_top_keys:
        errors.append("top-level keys must be sorted and complete")

    if backlog.get("task_id") != TASK_ID:
        errors.append("task_id must match PMBOT roadmap 003")
    if backlog.get("backlog_id") != BACKLOG_ID:
        errors.append("backlog_id must match the static artifact id")
    if backlog.get("contract_version") != CONTRACT_VERSION:
        errors.append("contract_version must match the next 20 backlog contract")
    if backlog.get("run_mode") != RUN_MODE:
        errors.append("run_mode must remain local static")
    if backlog.get("created_at") != CREATED_AT:
        errors.append("created_at must remain fixed for deterministic review")
    if backlog.get("local_only") is not True:
        errors.append("local_only must be true")
    if backlog.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if backlog.get("operator_review", {}).get("status") != OPERATOR_REVIEW_STATUS:
        errors.append("operator_review.status must be pending_operator_review")
    if backlog.get("errors") != []:
        errors.append("errors must be empty")
    if backlog.get("warnings") != []:
        errors.append("warnings must be empty")
    if backlog.get("required_validation_commands") != list(REQUIRED_VALIDATION_COMMANDS):
        errors.append("required_validation_commands must match acceptance checks")
    if backlog.get("safety_boundaries") != SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match closed local-only defaults")

    task_records = backlog.get("task_records")
    if not isinstance(task_records, list):
        errors.append("task_records must be a list")
        task_records = []

    if len(task_records) != 20:
        errors.append("task_records must contain exactly 20 records")

    task_ids = [record.get("task_id") for record in task_records if isinstance(record, dict)]
    if task_ids != [record["task_id"] for record in NEXT_TWENTY_TASK_RECORDS]:
        errors.append("task_records must match the fixed next 20 task id order")
    if len(set(task_ids)) != len(task_ids):
        errors.append("task_records.task_id values must be unique")

    for index, record in enumerate(task_records, start=1):
        if not isinstance(record, dict):
            errors.append(f"task_records[{index - 1}] must be an object")
            continue
        if set(record) != _expected_task_record_keys():
            errors.append(f"task_records[{index - 1}] keys must match the task record contract")
        if record.get("record_index") != index:
            errors.append(f"task_records[{index - 1}].record_index must be {index}")
        if record.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"task_records[{index - 1}].operator_review_status must be pending_operator_review")
        _validate_local_reference(record.get("local_reference"), f"task_records[{index - 1}].local_reference", errors)

    source_artifacts = backlog.get("source_artifacts")
    if not isinstance(source_artifacts, list):
        errors.append("source_artifacts must be a list")
        source_artifacts = []
    if source_artifacts != [dict(artifact) for artifact in SOURCE_ARTIFACTS]:
        errors.append("source_artifacts must match the fixed local source records")
    for index, artifact in enumerate(source_artifacts):
        if not isinstance(artifact, dict):
            errors.append(f"source_artifacts[{index}] must be an object")
            continue
        if set(artifact) != _expected_source_artifact_keys():
            errors.append(f"source_artifacts[{index}] keys must match the source artifact contract")
        if artifact.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"source_artifacts[{index}].operator_review_status must be pending_operator_review")
        _validate_local_reference(artifact.get("local_reference"), f"source_artifacts[{index}].local_reference", errors)

    if backlog.get("summary_counts") != _expected_summary_counts(task_records, source_artifacts):
        errors.append("summary_counts must match task and source artifact totals")

    blocked_paths = find_blocked_output_terms(backlog)
    if blocked_paths:
        errors.append(f"blocked guidance/scoring term detected outside task ids or local paths: {blocked_paths[0]}")

    return ValidationResult(valid=not errors, errors=tuple(errors))


def render_operator_report(backlog: dict) -> str:
    validation = validate_next_20_task_backlog(backlog)
    if not validation.valid:
        raise Next20TaskBacklogValidationError("; ".join(validation.errors))

    lines = [
        "# PMBOT Next 20 Task Backlog",
        "",
        f"Task: `{backlog['task_id']}`",
        f"Backlog: `{backlog['backlog_name']}`",
        f"Contract: `{backlog['contract_version']}`",
        f"Run mode: `{backlog['run_mode']}`",
        f"Operator review: `{backlog['operator_review']['status']}`",
        "",
        "## Purpose",
        "",
        "This report renders the deterministic local backlog artifact for operator review. It uses static local constants and does not read external services.",
        "",
        "## Backlog Records",
        "",
        "| # | Task ID | Workstream | Artifact Family | Local Reference | Review State |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in backlog["task_records"]:
        lines.append(
            "| {record_index} | `{task_id}` | `{workstream}` | `{artifact_family}` | `{local_reference}` | `{operator_review_status}` |".format(
                **record
            )
        )

    lines.extend(
        [
            "",
            "## Source Artifacts",
            "",
            "| Artifact ID | Role | Local Reference | Review State |",
            "| --- | --- | --- | --- |",
        ]
    )
    for artifact in backlog["source_artifacts"]:
        lines.append(
            "| `{artifact_id}` | `{record_role}` | `{local_reference}` | `{operator_review_status}` |".format(
                **artifact
            )
        )

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local files and static fixtures only.",
            "- No network calls.",
            "- No LLM provider calls.",
            "- No external market API calls.",
            "- No authenticated endpoint use.",
            "- No credential, wallet, signing material, order, payment, or transaction endpoint use.",
            "- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.",
            "- No forecast scoring, action guidance, or selection advice.",
            "- This backlog is not execution approval and is not runtime input.",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the static PMBOT next 20 task backlog artifact.")
    parser.add_argument("--output-backlog", type=Path, required=True)
    parser.add_argument("--output-report", type=Path)
    args = parser.parse_args(argv)

    backlog = build_next_20_task_backlog()
    write_json(args.output_backlog, backlog)
    if args.output_report is not None:
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        args.output_report.write_text(render_operator_report(backlog), encoding="utf-8")
    return 0


def _expected_backlog_keys() -> set[str]:
    return {
        "backlog_id",
        "backlog_name",
        "contract_version",
        "created_at",
        "errors",
        "generator",
        "local_only",
        "operator_review",
        "operator_review_required",
        "required_validation_commands",
        "run_mode",
        "safety_boundaries",
        "source_artifacts",
        "summary_counts",
        "task_id",
        "task_records",
        "warnings",
    }


def _expected_source_artifact_keys() -> set[str]:
    return {"artifact_id", "local_reference", "operator_review_status", "record_role", "record_state"}


def _expected_task_record_keys() -> set[str]:
    return {
        "artifact_family",
        "local_reference",
        "operator_review_status",
        "record_index",
        "review_note",
        "task_id",
        "workstream",
    }


def _expected_summary_counts(task_records: list[dict], source_artifacts: list[dict]) -> dict:
    local_references = {
        record.get("local_reference")
        for record in task_records
        if isinstance(record, dict) and isinstance(record.get("local_reference"), str)
    }
    local_references.update(
        artifact.get("local_reference")
        for artifact in source_artifacts
        if isinstance(artifact, dict) and isinstance(artifact.get("local_reference"), str)
    )
    return {
        "local_references": len(local_references),
        "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
        "source_artifacts": len(source_artifacts),
        "task_records": len(task_records),
        "task_records_pending_operator_review": sum(
            1
            for record in task_records
            if isinstance(record, dict) and record.get("operator_review_status") == OPERATOR_REVIEW_STATUS
        ),
        "warnings": 0,
    }


def _validate_local_reference(value: object, path: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{path} must be a string")
        return
    if "://" in value:
        errors.append(f"{path} must be a local path")
    if not value.startswith(ALLOWED_LOCAL_PREFIXES):
        errors.append(f"{path} must stay under allowed local prefixes")


def find_blocked_output_terms(value: object, path: str = "$") -> list[str]:
    blocked_tokens = {
        "advice",
        "buy",
        "confidence",
        "edge",
        "enter",
        "ev",
        "exit",
        "forecast",
        "guidance",
        "hold",
        "odds",
        "pick",
        "probability",
        "recommendation",
        "recommendations",
        "score",
        "scoring",
        "selection",
        "sell",
        "side",
        "stake",
        "wager",
    }
    ignored_value_paths = ("task_id", "local_reference")
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_token(str(key), blocked_tokens):
                hits.append(key_path)
            if key in ignored_value_paths:
                continue
            hits.extend(find_blocked_output_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(find_blocked_output_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_token(value, blocked_tokens):
        hits.append(path)
    return hits


def _has_token(value: str, blocked_tokens: set[str]) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & blocked_tokens)


if __name__ == "__main__":
    raise SystemExit(main())
