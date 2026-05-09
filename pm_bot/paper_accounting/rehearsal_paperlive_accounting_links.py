from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from pm_bot.paper_accounting.paper_accounting_ledger import (
    FORBIDDEN_DECISION_TOKENS,
    FORBIDDEN_LOCAL_REFERENCE_PREFIXES,
    OPERATOR_REVIEW_STATUS,
    ValidationResult,
)

TASK_ID = "PMBOT-REHEARSAL-015-REHEARSAL-PAPERLIVE-ACCOUNTING-LINKS-LOCAL-ONLY"
LINK_SET_ID = "pmbot-rehearsal-paperlive-accounting-links-001"
LINKS_CONTRACT_VERSION = "pmbot_rehearsal_paperlive_accounting_links.v1"
LINKS_RUN_MODE = "local_static_rehearsal_paperlive_accounting_links"
LINK_STATE = "descriptive_rehearsal_paperlive_accounting_link"
CREATED_AT = "2026-05-09T10:00:00Z"

REHEARSAL_PACKET_PATH = "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json"
OBSERVATION_REPLAY_PATH = "pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json"
PAPERLIVE_RECONCILIATION_PATH = "pm_bot/paper_accounting/samples/paperlive_accounting_reconciliation.fixture.json"
PAPER_ACCOUNTING_LEDGER_PATH = "pm_bot/paper_accounting/samples/paper_accounting_ledger.fixture.json"
PAPER_ACCOUNTING_VALIDATION_PATH = "pm_bot/paper_accounting/samples/paper_accounting_validation.fixture.json"
PAPER_ACCOUNTING_SESSION_SUMMARY_PATH = "pm_bot/paper_accounting/samples/paper_accounting_session_summary.fixture.json"
SAMPLE_LINKS_PATH = "pm_bot/paper_accounting/samples/rehearsal_paperlive_accounting_links.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/paper_accounting/samples/rehearsal_paperlive_accounting_links.fixture.md"

REQUIRED_VALIDATION_COMMANDS = (
    "python -m compileall pm_bot tests",
    "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
)
ALLOWED_LOCAL_REFERENCE_PREFIXES = (
    "docs/",
    "pm_bot/paper_accounting/samples/",
    "pm_bot/tests/",
    "tests/",
)
EXPECTED_LINK_FIELDS = (
    "accounting_artifact_ids",
    "accounting_entry_count",
    "accounting_handling",
    "link_id",
    "link_state",
    "operator_review_status",
    "paperlive_accounting_record_ids",
    "rehearsal_artifact_ids",
    "rehearsal_record_ids",
    "review_checks",
    "value_policy",
)
EXPECTED_REHEARSAL_RECORD_ID_FIELDS = (
    "observation_record_id",
    "observation_replay_record_id",
    "packet_record_id",
)
EXPECTED_PAPERLIVE_ACCOUNTING_RECORD_ID_FIELDS = (
    "accounting_entry_ids",
    "accounting_ledger_id",
    "paperlive_record_id",
    "reconciliation_id",
    "reconciliation_row_id",
    "session_review_entry_ids",
    "validation_row_ids",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "account_change_instruction_allowed": False,
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_fixtures_only": True,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_instruction_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "openrouter_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "paperlive_execution_allowed": False,
    "polymarket_api_calls_allowed": False,
    "resident_process_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "timed_automation_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


class RehearsalPaperliveAccountingLinksError(ValueError):
    def __init__(self, errors: tuple[str, ...]):
        super().__init__("; ".join(errors))
        self.errors = errors


def load_rehearsal_paperlive_accounting_links(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RehearsalPaperliveAccountingLinksError(("rehearsal paperlive accounting links must be a JSON object",))
    return payload


def load_rehearsal_paperlive_accounting_link_inputs() -> dict[str, dict[str, Any]]:
    return {
        "accounting_ledger": _load_local_json_object(PAPER_ACCOUNTING_LEDGER_PATH),
        "accounting_session_summary": _load_local_json_object(PAPER_ACCOUNTING_SESSION_SUMMARY_PATH),
        "accounting_validation": _load_local_json_object(PAPER_ACCOUNTING_VALIDATION_PATH),
        "observation_replay": _load_local_json_object(OBSERVATION_REPLAY_PATH),
        "paperlive_reconciliation": _load_local_json_object(PAPERLIVE_RECONCILIATION_PATH),
        "rehearsal_packet": _load_local_json_object(REHEARSAL_PACKET_PATH),
    }


def build_rehearsal_paperlive_accounting_links(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    _validate_input_consistency(inputs)

    packet = inputs["rehearsal_packet"]
    replay = inputs["observation_replay"]
    reconciliation = inputs["paperlive_reconciliation"]
    ledger = inputs["accounting_ledger"]
    validation = inputs["accounting_validation"]
    session_summary = inputs["accounting_session_summary"]

    packet_record = packet["paperlive_rehearsal_records"][0]
    replay_record = replay["observation_replay_records"][0]
    reconciliation_row = reconciliation["paperlive_reconciliation_rows"][0]
    accounting_entry_ids = list(reconciliation_row["accounting_entry_ids"])
    validation_by_entry = {row["entry_id"]: row for row in validation["record_validation_rows"]}
    session_by_entry = {row["entry_id"]: row for row in session_summary["session_review_rows"]}

    validation_row_ids = [
        validation_by_entry[entry_id]["validation_row_id"]
        for entry_id in accounting_entry_ids
        if entry_id in validation_by_entry
    ]
    session_review_entry_ids = [entry_id for entry_id in accounting_entry_ids if entry_id in session_by_entry]

    rehearsal_artifacts = [
        _build_artifact_record(
            artifact_id="crypto_paperlive_rehearsal_packet_fixture",
            artifact_role="paperlive_rehearsal_packet",
            artifact_type="json_fixture",
            local_reference=REHEARSAL_PACKET_PATH,
            record_collection="paperlive_rehearsal_records",
            record_id_field="packet_record_id",
        ),
        _build_artifact_record(
            artifact_id="crypto_paperlive_observation_replay_fixture",
            artifact_role="paperlive_observation_replay",
            artifact_type="json_fixture",
            local_reference=OBSERVATION_REPLAY_PATH,
            record_collection="observation_replay_records",
            record_id_field="replay_record_id",
        ),
    ]
    accounting_artifacts = [
        _build_artifact_record(
            artifact_id="paperlive_accounting_reconciliation_sample",
            artifact_role="paperlive_accounting_reconciliation",
            artifact_type="json_sample",
            local_reference=PAPERLIVE_RECONCILIATION_PATH,
            record_collection="paperlive_reconciliation_rows",
            record_id_field="row_id",
        ),
        _build_artifact_record(
            artifact_id="paper_accounting_ledger_sample",
            artifact_role="paper_accounting_ledger",
            artifact_type="json_sample",
            local_reference=PAPER_ACCOUNTING_LEDGER_PATH,
            record_collection="accounting_entries",
            record_id_field="entry_id",
        ),
        _build_artifact_record(
            artifact_id="paper_accounting_validation_sample",
            artifact_role="paper_accounting_validation",
            artifact_type="json_sample",
            local_reference=PAPER_ACCOUNTING_VALIDATION_PATH,
            record_collection="record_validation_rows",
            record_id_field="validation_row_id",
        ),
        _build_artifact_record(
            artifact_id="paper_accounting_session_summary_sample",
            artifact_role="paper_accounting_session_summary",
            artifact_type="json_sample",
            local_reference=PAPER_ACCOUNTING_SESSION_SUMMARY_PATH,
            record_collection="session_review_rows",
            record_id_field="entry_id",
        ),
    ]
    paperlive_accounting_links = [
        {
            "accounting_artifact_ids": [artifact["artifact_id"] for artifact in accounting_artifacts],
            "accounting_entry_count": len(accounting_entry_ids),
            "accounting_handling": reconciliation_row["accounting_handling"],
            "link_id": f"{LINK_SET_ID}.sample.btc_threshold.paperlive_accounting",
            "link_state": LINK_STATE,
            "operator_review_status": OPERATOR_REVIEW_STATUS,
            "paperlive_accounting_record_ids": {
                "accounting_entry_ids": accounting_entry_ids,
                "accounting_ledger_id": reconciliation_row["accounting_ledger_id"],
                "paperlive_record_id": reconciliation_row["paperlive_record_id"],
                "reconciliation_id": reconciliation["reconciliation_id"],
                "reconciliation_row_id": reconciliation_row["row_id"],
                "session_review_entry_ids": session_review_entry_ids,
                "validation_row_ids": validation_row_ids,
            },
            "rehearsal_artifact_ids": [artifact["artifact_id"] for artifact in rehearsal_artifacts],
            "rehearsal_record_ids": {
                "observation_record_id": packet_record["observation_record_id"],
                "observation_replay_record_id": replay_record["replay_record_id"],
                "packet_record_id": packet_record["packet_record_id"],
            },
            "review_checks": [
                _review_check("rehearsal_packet_record_link", "Confirm packet record ID is present in the local rehearsal packet fixture."),
                _review_check("observation_replay_record_link", "Confirm replay row references the same packet and observation records."),
                _review_check("paperlive_reconciliation_record_link", "Confirm reconciliation row references the same local paperlive observation record."),
                _review_check("paper_accounting_record_link", "Confirm linked paper accounting entry IDs remain present in local accounting samples."),
            ],
            "value_policy": "record_identifiers_only_values_remain_in_local_artifacts",
        }
    ]
    validation_command_records = [
        {
            "command_label": REQUIRED_VALIDATION_COMMANDS[0],
            "local_reference": "pm_bot/tests/test_rehearsal_paperlive_accounting_links.py",
            "operator_review_status": OPERATOR_REVIEW_STATUS,
            "status": "not_run_static_record",
        },
        {
            "command_label": REQUIRED_VALIDATION_COMMANDS[1],
            "local_reference": "tests/test_codex_queue_pmbot_templates.py",
            "operator_review_status": OPERATOR_REVIEW_STATUS,
            "status": "not_run_static_record",
        },
    ]

    draft = {
        "accounting_artifacts": accounting_artifacts,
        "contract_version": LINKS_CONTRACT_VERSION,
        "created_at": CREATED_AT,
        "errors": [],
        "link_fields": list(EXPECTED_LINK_FIELDS),
        "link_set_id": LINK_SET_ID,
        "local_only": True,
        "operator_review": {
            "reviewed_at": None,
            "reviewed_by": None,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "operator_review_steps": [
            "Confirm rehearsal packet and replay record IDs resolve to local static fixtures.",
            "Confirm paperlive reconciliation rows resolve to local paper accounting samples.",
            "Confirm accounting entry, validation, and session rows remain pending operator review.",
            "Confirm numeric source values remain in referenced local artifacts rather than this link set.",
            "Confirm closed endpoint, wallet, order, runtime, worker, scheduler, and browser boundaries.",
        ],
        "paperlive_accounting_links": paperlive_accounting_links,
        "rehearsal_artifacts": rehearsal_artifacts,
        "required_validation_commands": list(REQUIRED_VALIDATION_COMMANDS),
        "run_mode": LINKS_RUN_MODE,
        "safety_boundaries": deepcopy(EXPECTED_SAFETY_BOUNDARIES),
        "summary_counts": {},
        "task_id": TASK_ID,
        "validation_command_records": validation_command_records,
        "warnings": [],
    }
    draft["summary_counts"] = _build_summary_counts(draft)
    draft["build_id"] = f"{LINK_SET_ID}-{_stable_digest(draft)}"
    return dict(sorted(draft.items()))


def validate_rehearsal_paperlive_accounting_links(link_set: Any) -> ValidationResult:
    errors: list[str] = []
    if not isinstance(link_set, dict):
        return ValidationResult(False, ("rehearsal paperlive accounting links must be an object",))

    errors.extend(_find_forbidden_decision_terms(link_set, "rehearsal_paperlive_accounting_links"))
    required_fields = {
        "accounting_artifacts",
        "build_id",
        "contract_version",
        "created_at",
        "errors",
        "link_fields",
        "link_set_id",
        "local_only",
        "operator_review",
        "operator_review_required",
        "operator_review_steps",
        "paperlive_accounting_links",
        "rehearsal_artifacts",
        "required_validation_commands",
        "run_mode",
        "safety_boundaries",
        "summary_counts",
        "task_id",
        "validation_command_records",
        "warnings",
    }
    _require_keys(link_set, required_fields, "rehearsal_paperlive_accounting_links", errors)
    if required_fields - set(link_set):
        return ValidationResult(False, tuple(errors))

    if link_set["task_id"] != TASK_ID:
        errors.append(f"task_id must be {TASK_ID}")
    if link_set["link_set_id"] != LINK_SET_ID:
        errors.append(f"link_set_id must be {LINK_SET_ID}")
    if link_set["contract_version"] != LINKS_CONTRACT_VERSION:
        errors.append(f"contract_version must be {LINKS_CONTRACT_VERSION}")
    if link_set["run_mode"] != LINKS_RUN_MODE:
        errors.append(f"run_mode must be {LINKS_RUN_MODE}")
    if link_set["created_at"] != CREATED_AT:
        errors.append(f"created_at must be {CREATED_AT}")
    if link_set["local_only"] is not True:
        errors.append("local_only must be true")
    if link_set["operator_review_required"] is not True:
        errors.append("operator_review_required must be true")
    if link_set["safety_boundaries"] != EXPECTED_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match closed local-only paper mode boundaries")
    if link_set["required_validation_commands"] != list(REQUIRED_VALIDATION_COMMANDS):
        errors.append("required_validation_commands must match acceptance commands")
    if link_set["link_fields"] != list(EXPECTED_LINK_FIELDS):
        errors.append("link_fields must match the fixed rehearsal paperlive accounting link fields")
    if not isinstance(link_set["operator_review"], dict) or link_set["operator_review"].get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"operator_review.status must be {OPERATOR_REVIEW_STATUS}")
    if not isinstance(link_set["errors"], list) or link_set["errors"]:
        errors.append("errors must be an empty list")
    if not isinstance(link_set["warnings"], list):
        errors.append("warnings must be a list")

    artifact_rows = _validate_artifact_rows(link_set.get("rehearsal_artifacts"), "rehearsal_artifacts", errors)
    artifact_rows.update(_validate_artifact_rows(link_set.get("accounting_artifacts"), "accounting_artifacts", errors))
    _validate_validation_command_records(link_set.get("validation_command_records"), errors)
    _validate_link_rows(link_set.get("paperlive_accounting_links"), artifact_rows, errors)

    expected_summary_counts = _build_summary_counts(link_set)
    if link_set.get("summary_counts") != expected_summary_counts:
        errors.append("summary_counts must match link set content")

    expected_build_id = f"{LINK_SET_ID}-{_stable_digest({key: value for key, value in link_set.items() if key != 'build_id'})}"
    if link_set.get("build_id") != expected_build_id:
        errors.append("build_id must match deterministic link set digest")

    return ValidationResult(not errors, tuple(errors))


def build_operator_report(link_set: dict[str, Any]) -> str:
    lines = [
        "# PMBOT Rehearsal Paperlive Accounting Links",
        "",
        f"Link set: `{link_set['link_set_id']}`",
        f"Build ID: `{link_set['build_id']}`",
        f"Run mode: `{link_set['run_mode']}`",
        f"Operator review: `{link_set['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Rehearsal artifacts: {link_set['summary_counts']['rehearsal_artifacts']}",
        f"- Accounting artifacts: {link_set['summary_counts']['accounting_artifacts']}",
        f"- Paperlive accounting links: {link_set['summary_counts']['paperlive_accounting_links']}",
        f"- Accounting entry links: {link_set['summary_counts']['accounting_entry_links']}",
        f"- Local references: {link_set['summary_counts']['local_references']}",
        f"- Warnings: {link_set['summary_counts']['warnings']}",
        "",
        "## Rehearsal Artifacts",
        "",
    ]
    for artifact in link_set["rehearsal_artifacts"]:
        lines.append(
            f"- `{artifact['artifact_id']}`: {artifact['record_count']} records from `{artifact['local_reference']}`."
        )
    lines.extend(["", "## Accounting Artifacts", ""])
    for artifact in link_set["accounting_artifacts"]:
        lines.append(
            f"- `{artifact['artifact_id']}`: {artifact['record_count']} records from `{artifact['local_reference']}`."
        )
    lines.extend(["", "## Links", ""])
    for link in link_set["paperlive_accounting_links"]:
        record_ids = link["paperlive_accounting_record_ids"]
        lines.append(
            f"- `{link['link_id']}` connects packet `{link['rehearsal_record_ids']['packet_record_id']}` "
            f"to reconciliation row `{record_ids['reconciliation_row_id']}` with "
            f"{link['accounting_entry_count']} accounting entry links."
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixtures and static paper accounting samples only.",
            "- No network, provider, external market API, authenticated endpoint, wallet, order, transaction, runtime, worker, scheduler, or browser use.",
            "- Values remain in referenced local artifacts; this link set records identifiers for operator review.",
            "- Not execution approval and not runtime input.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build local-only rehearsal paperlive accounting links for PMBOT operator review."
    )
    parser.add_argument("--output-links", required=True, help="Path where the JSON link set should be written.")
    parser.add_argument("--output-report", required=True, help="Path where the Markdown report should be written.")
    args = parser.parse_args(argv)

    link_set = build_rehearsal_paperlive_accounting_links(load_rehearsal_paperlive_accounting_link_inputs())
    validation = validate_rehearsal_paperlive_accounting_links(link_set)
    if not validation.valid:
        raise RehearsalPaperliveAccountingLinksError(validation.errors)

    output_links = Path(args.output_links)
    output_report = Path(args.output_report)
    output_links.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_links.write_text(json.dumps(link_set, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_report.write_text(build_operator_report(link_set), encoding="utf-8")
    return 0


def _validate_input_consistency(inputs: dict[str, dict[str, Any]]) -> None:
    errors: list[str] = []
    required_keys = {
        "accounting_ledger",
        "accounting_session_summary",
        "accounting_validation",
        "observation_replay",
        "paperlive_reconciliation",
        "rehearsal_packet",
    }
    missing = sorted(required_keys - set(inputs))
    if missing:
        raise RehearsalPaperliveAccountingLinksError((f"inputs missing required keys: {', '.join(missing)}",))

    packet_records = inputs["rehearsal_packet"].get("paperlive_rehearsal_records")
    replay_records = inputs["observation_replay"].get("observation_replay_records")
    reconciliation_rows = inputs["paperlive_reconciliation"].get("paperlive_reconciliation_rows")
    ledger_entries = inputs["accounting_ledger"].get("accounting_entries")
    validation_rows = inputs["accounting_validation"].get("record_validation_rows")
    session_rows = inputs["accounting_session_summary"].get("session_review_rows")

    if not isinstance(packet_records, list) or len(packet_records) != 1:
        errors.append("rehearsal_packet must contain one paperlive_rehearsal_record")
    if not isinstance(replay_records, list) or len(replay_records) != 1:
        errors.append("observation_replay must contain one observation_replay_record")
    if not isinstance(reconciliation_rows, list) or len(reconciliation_rows) != 1:
        errors.append("paperlive_reconciliation must contain one paperlive_reconciliation_row")
    if not isinstance(ledger_entries, list):
        errors.append("accounting_ledger.accounting_entries must be a list")
    if not isinstance(validation_rows, list):
        errors.append("accounting_validation.record_validation_rows must be a list")
    if not isinstance(session_rows, list):
        errors.append("accounting_session_summary.session_review_rows must be a list")
    if errors:
        raise RehearsalPaperliveAccountingLinksError(tuple(errors))

    packet_record = packet_records[0]
    replay_record = replay_records[0]
    reconciliation_row = reconciliation_rows[0]
    if replay_record.get("source_packet_record_id") != packet_record.get("packet_record_id"):
        errors.append("observation replay source_packet_record_id must match rehearsal packet record")
    if replay_record.get("source_observation_record_id") != packet_record.get("observation_record_id"):
        errors.append("observation replay source_observation_record_id must match rehearsal packet observation record")
    if reconciliation_row.get("paperlive_record_id") != packet_record.get("observation_record_id"):
        errors.append("paperlive reconciliation row must reference the rehearsal packet observation record")
    if reconciliation_row.get("accounting_ledger_id") != inputs["accounting_ledger"].get("ledger_id"):
        errors.append("paperlive reconciliation row accounting_ledger_id must match paper accounting ledger")

    ledger_entry_ids = {entry.get("entry_id") for entry in ledger_entries if isinstance(entry, dict)}
    for entry_id in reconciliation_row.get("accounting_entry_ids", []):
        if entry_id not in ledger_entry_ids:
            errors.append(f"accounting entry id is missing from paper accounting ledger: {entry_id}")
    if errors:
        raise RehearsalPaperliveAccountingLinksError(tuple(errors))


def _build_artifact_record(
    *,
    artifact_id: str,
    artifact_role: str,
    artifact_type: str,
    local_reference: str,
    record_collection: str,
    record_id_field: str,
) -> dict[str, Any]:
    payload = _load_local_json_object(local_reference)
    records = payload.get(record_collection, [])
    if not isinstance(records, list):
        records = []
    path = Path(local_reference)
    data = path.read_bytes()
    record_ids = [
        record[record_id_field]
        for record in records
        if isinstance(record, dict) and isinstance(record.get(record_id_field), str)
    ]
    return {
        "artifact_id": artifact_id,
        "artifact_role": artifact_role,
        "artifact_type": artifact_type,
        "byte_count": len(data),
        "content_sha256": hashlib.sha256(data).hexdigest(),
        "contract_version": str(payload.get("contract_version", "local_static_sample")),
        "local_reference": _normalize_local_reference(local_reference),
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "present": path.exists(),
        "record_collection": record_collection,
        "record_count": len(record_ids),
        "record_ids": record_ids,
    }


def _review_check(check_id: str, review_label: str) -> dict[str, str]:
    return {
        "check_id": check_id,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "review_label": review_label,
    }


def _validate_artifact_rows(artifacts: Any, path: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(artifacts, list):
        errors.append(f"{path} must be a list")
        return {}
    artifact_rows: dict[str, dict[str, Any]] = {}
    required_fields = {
        "artifact_id",
        "artifact_role",
        "artifact_type",
        "byte_count",
        "content_sha256",
        "contract_version",
        "local_reference",
        "operator_review_status",
        "present",
        "record_collection",
        "record_count",
        "record_ids",
    }
    for artifact_index, artifact in enumerate(artifacts):
        artifact_path = f"{path}[{artifact_index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{artifact_path} must be an object")
            continue
        _require_keys(artifact, required_fields, artifact_path, errors)
        if required_fields - set(artifact):
            continue
        artifact_id = artifact.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            errors.append(f"{artifact_path}.artifact_id must be a non-empty string")
            continue
        if artifact_id in artifact_rows:
            errors.append(f"{artifact_path}.artifact_id must be unique")
        artifact_rows[artifact_id] = artifact
        if artifact.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{artifact_path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if artifact.get("present") is not True:
            errors.append(f"{artifact_path}.present must be true")
        if not _is_allowed_local_reference(artifact.get("local_reference")):
            errors.append(f"{artifact_path}.local_reference must stay under allowed local paths")
            continue
        local_path = Path(str(artifact["local_reference"]))
        if not local_path.exists():
            errors.append(f"{artifact_path}.local_reference must exist")
            continue
        data = local_path.read_bytes()
        if artifact.get("byte_count") != len(data):
            errors.append(f"{artifact_path}.byte_count must match local bytes")
        if artifact.get("content_sha256") != hashlib.sha256(data).hexdigest():
            errors.append(f"{artifact_path}.content_sha256 must match local bytes")
        if not isinstance(artifact.get("record_ids"), list):
            errors.append(f"{artifact_path}.record_ids must be a list")
        elif artifact.get("record_count") != len(artifact["record_ids"]):
            errors.append(f"{artifact_path}.record_count must match record_ids length")
    return artifact_rows


def _validate_link_rows(links: Any, artifacts: dict[str, dict[str, Any]], errors: list[str]) -> None:
    if not isinstance(links, list) or not links:
        errors.append("paperlive_accounting_links must be a non-empty list")
        return
    observed_link_ids: set[str] = set()
    for link_index, link in enumerate(links):
        path = f"paperlive_accounting_links[{link_index}]"
        if not isinstance(link, dict):
            errors.append(f"{path} must be an object")
            continue
        _require_keys(link, set(EXPECTED_LINK_FIELDS), path, errors)
        if set(EXPECTED_LINK_FIELDS) - set(link):
            continue
        link_id = link.get("link_id")
        if not isinstance(link_id, str) or not link_id:
            errors.append(f"{path}.link_id must be a non-empty string")
        elif link_id in observed_link_ids:
            errors.append(f"{path}.link_id must be unique")
        observed_link_ids.add(str(link_id))
        if link.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if link.get("link_state") != LINK_STATE:
            errors.append(f"{path}.link_state must be {LINK_STATE}")
        if link.get("value_policy") != "record_identifiers_only_values_remain_in_local_artifacts":
            errors.append(f"{path}.value_policy must retain values in local artifacts")
        _validate_link_artifact_ids(link.get("rehearsal_artifact_ids"), artifacts, f"{path}.rehearsal_artifact_ids", errors)
        _validate_link_artifact_ids(link.get("accounting_artifact_ids"), artifacts, f"{path}.accounting_artifact_ids", errors)
        _validate_record_id_object(
            link.get("rehearsal_record_ids"),
            EXPECTED_REHEARSAL_RECORD_ID_FIELDS,
            f"{path}.rehearsal_record_ids",
            errors,
        )
        _validate_record_id_object(
            link.get("paperlive_accounting_record_ids"),
            EXPECTED_PAPERLIVE_ACCOUNTING_RECORD_ID_FIELDS,
            f"{path}.paperlive_accounting_record_ids",
            errors,
        )
        accounting_ids = link["paperlive_accounting_record_ids"].get("accounting_entry_ids", [])
        if not isinstance(accounting_ids, list):
            errors.append(f"{path}.paperlive_accounting_record_ids.accounting_entry_ids must be a list")
            accounting_ids = []
        if link.get("accounting_entry_count") != len(accounting_ids):
            errors.append(f"{path}.accounting_entry_count must match accounting_entry_ids length")
        _validate_review_checks(link.get("review_checks"), path, errors)
        _validate_link_record_ids_exist(link, artifacts, path, errors)


def _validate_link_artifact_ids(value: Any, artifacts: dict[str, dict[str, Any]], path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path} must be a non-empty list")
        return
    for artifact_id in value:
        if artifact_id not in artifacts:
            errors.append(f"{path} must reference known artifact ids")


def _validate_record_id_object(value: Any, fields: tuple[str, ...], path: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return
    if tuple(value.keys()) != fields:
        errors.append(f"{path} must have fixed fields {fields}")
    for field in fields:
        field_value = value.get(field)
        if field.endswith("_ids"):
            if not isinstance(field_value, list) or not all(isinstance(item, str) for item in field_value):
                errors.append(f"{path}.{field} must be a list of strings")
        elif not isinstance(field_value, str) or not field_value:
            errors.append(f"{path}.{field} must be a non-empty string")


def _validate_review_checks(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path}.review_checks must be a non-empty list")
        return
    for check_index, check in enumerate(value):
        check_path = f"{path}.review_checks[{check_index}]"
        if not isinstance(check, dict):
            errors.append(f"{check_path} must be an object")
            continue
        if check.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{check_path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")


def _validate_link_record_ids_exist(
    link: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
    path: str,
    errors: list[str],
) -> None:
    artifact_record_ids = {
        artifact_id: set(artifact.get("record_ids", []))
        for artifact_id, artifact in artifacts.items()
        if isinstance(artifact.get("record_ids"), list)
    }
    rehearsal_ids = link["rehearsal_record_ids"]
    accounting_ids = link["paperlive_accounting_record_ids"]
    existence_checks = (
        ("crypto_paperlive_rehearsal_packet_fixture", rehearsal_ids["packet_record_id"]),
        ("crypto_paperlive_observation_replay_fixture", rehearsal_ids["observation_replay_record_id"]),
        ("paperlive_accounting_reconciliation_sample", accounting_ids["reconciliation_row_id"]),
        ("paper_accounting_ledger_sample", *accounting_ids["accounting_entry_ids"]),
        ("paper_accounting_validation_sample", *accounting_ids["validation_row_ids"]),
        ("paper_accounting_session_summary_sample", *accounting_ids["session_review_entry_ids"]),
    )
    for artifact_id, *record_ids in existence_checks:
        known_ids = artifact_record_ids.get(artifact_id, set())
        for record_id in record_ids:
            if record_id not in known_ids:
                errors.append(f"{path} record id {record_id} must exist in {artifact_id}")


def _validate_validation_command_records(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("validation_command_records must be a list")
        return
    if [record.get("command_label") for record in value if isinstance(record, dict)] != list(REQUIRED_VALIDATION_COMMANDS):
        errors.append("validation_command_records must mirror required_validation_commands")
    for index, record in enumerate(value):
        path = f"validation_command_records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{path} must be an object")
            continue
        if record.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if record.get("status") != "not_run_static_record":
            errors.append(f"{path}.status must be not_run_static_record")
        if not _is_allowed_local_reference(record.get("local_reference")):
            errors.append(f"{path}.local_reference must stay under allowed local paths")


def _build_summary_counts(link_set: dict[str, Any]) -> dict[str, int]:
    local_references = set(_collect_values_for_key(link_set, "local_reference"))
    links = link_set.get("paperlive_accounting_links", [])
    return {
        "accounting_artifacts": len(link_set.get("accounting_artifacts", [])),
        "accounting_entry_links": sum(
            len(link["paperlive_accounting_record_ids"]["accounting_entry_ids"])
            for link in links
            if isinstance(link, dict) and isinstance(link.get("paperlive_accounting_record_ids"), dict)
        ),
        "link_fields": len(link_set.get("link_fields", [])),
        "local_references": len(local_references),
        "operator_review_steps": len(link_set.get("operator_review_steps", [])),
        "paperlive_accounting_links": len(links),
        "rehearsal_artifacts": len(link_set.get("rehearsal_artifacts", [])),
        "rehearsal_record_links": sum(
            len(link.get("rehearsal_record_ids", {}))
            for link in links
            if isinstance(link, dict) and isinstance(link.get("rehearsal_record_ids"), dict)
        ),
        "required_validation_commands": len(link_set.get("required_validation_commands", [])),
        "review_checks": sum(
            len(link.get("review_checks", []))
            for link in links
            if isinstance(link, dict) and isinstance(link.get("review_checks"), list)
        ),
        "validation_command_records": len(link_set.get("validation_command_records", [])),
        "warnings": len(link_set.get("warnings", [])) if isinstance(link_set.get("warnings"), list) else 0,
    }


def _load_local_json_object(local_reference: str) -> dict[str, Any]:
    if not _is_allowed_local_reference(local_reference):
        raise RehearsalPaperliveAccountingLinksError((f"local_reference is outside allowed paths: {local_reference}",))
    path = Path(_normalize_local_reference(local_reference))
    if not path.exists():
        raise RehearsalPaperliveAccountingLinksError((f"local_reference does not exist: {local_reference}",))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RehearsalPaperliveAccountingLinksError((f"local_reference must contain a JSON object: {local_reference}",))
    return payload


def _is_allowed_local_reference(local_reference: Any) -> bool:
    if not isinstance(local_reference, str) or not local_reference:
        return False
    normalized = _normalize_local_reference(local_reference)
    if "://" in normalized or normalized.startswith("/") or Path(normalized).is_absolute():
        return False
    parts = [part for part in normalized.split("/") if part]
    if ".." in parts:
        return False
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in FORBIDDEN_LOCAL_REFERENCE_PREFIXES):
        return False
    return any(normalized.startswith(prefix) for prefix in ALLOWED_LOCAL_REFERENCE_PREFIXES)


def _normalize_local_reference(local_reference: str) -> str:
    return local_reference.replace("\\", "/")


def _stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


def _collect_values_for_key(value: object, key: str) -> list[str]:
    matches: list[str] = []
    if isinstance(value, dict):
        for nested_key, nested_value in value.items():
            if nested_key == key:
                matches.append(str(nested_value))
            matches.extend(_collect_values_for_key(nested_value, key))
    elif isinstance(value, list):
        for nested_value in value:
            matches.extend(_collect_values_for_key(nested_value, key))
    return matches


def _require_keys(value: dict[str, Any], required_fields: set[str], path: str, errors: list[str]) -> None:
    missing = sorted(required_fields - set(value))
    if missing:
        errors.append(f"{path} missing required fields: {', '.join(missing)}")


def _find_forbidden_decision_terms(value: Any, path: str) -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_forbidden_token(str(key)):
                hits.append(f"forbidden scoring/action field detected at {key_path}")
            if key in {"command_label", "local_reference", "required_validation_commands"}:
                continue
            hits.extend(_find_forbidden_decision_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_forbidden_decision_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_forbidden_token(value):
        hits.append(f"forbidden scoring/action text detected at {path}")
    return hits


def _has_forbidden_token(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & FORBIDDEN_DECISION_TOKENS)


if __name__ == "__main__":
    raise SystemExit(main())
