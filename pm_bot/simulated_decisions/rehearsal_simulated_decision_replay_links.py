from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TASK_ID = "PMBOT-REHEARSAL-016-REHEARSAL-SIMULATED-DECISION-REPLAY-LINKS-LOCAL-ONLY"
LINK_SET_ID = "pmbot-rehearsal-simulated-decision-replay-links-001"
LINKS_CONTRACT_VERSION = "pmbot_rehearsal_simulated_decision_replay_links.v1"
LINKS_RUN_MODE = "local_static_rehearsal_simulated_decision_replay_links"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
LINK_STATE = "descriptive_rehearsal_simulated_decision_replay_link"

_PACKAGE_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _PACKAGE_DIR.parents[1]
SAMPLE_LINKS_PATH = "pm_bot/simulated_decisions/samples/rehearsal_simulated_decision_replay_links.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/simulated_decisions/samples/rehearsal_simulated_decision_replay_links.fixture.md"

VALIDATION_REPLAY_PACKET_PATH = (
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_validation_replay_packet.valid.json"
)
CI_SAFE_VALIDATION_RUNNER_PATH = (
    "pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_ci_safe_validation_runner.valid.json"
)
REHEARSAL_ACCEPTANCE_REPORT_DOC_PATH = "docs/PMBOT_REHEARSAL_013_REHEARSAL_ACCEPTANCE_REPORT_LOCAL_ONLY.md"
REHEARSAL_SOURCE_QUALITY_LINKS_DOC_PATH = "docs/PMBOT_REHEARSAL_014_REHEARSAL_SOURCE_QUALITY_LINKS_LOCAL_ONLY.md"
REHEARSAL_PAPERLIVE_ACCOUNTING_LINKS_DOC_PATH = (
    "docs/PMBOT_REHEARSAL_015_REHEARSAL_PAPERLIVE_ACCOUNTING_LINKS_LOCAL_ONLY.md"
)
SIMULATED_DECISION_PACKET_PATH = "pm_bot/simulated_decisions/samples/simulated_decision_packet.fixture.json"
SIMULATED_DECISION_AUDIT_LEDGER_PATH = (
    "pm_bot/simulated_decisions/samples/simulated_decision_audit_ledger.fixture.json"
)
SIMULATED_DECISION_REPLAY_SUMMARY_PATH = (
    "pm_bot/simulated_decisions/samples/simulated_decision_replay_summary.fixture.json"
)
SIMULATED_DECISION_OUTCOME_REPLAY_LINKS_PATH = (
    "pm_bot/simulated_decisions/samples/simulated_decision_outcome_replay_links.fixture.json"
)

REQUIRED_VALIDATION_COMMANDS = (
    "python -m compileall pm_bot tests",
    "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
)
EXPECTED_LINK_FIELDS = (
    "link_id",
    "link_state",
    "link_basis",
    "rehearsal_artifact_ids",
    "rehearsal_record_ids",
    "simulated_decision_artifact_ids",
    "simulated_decision_record_ids",
    "replay_record_row_ids",
    "local_reference_pairs",
    "value_policy",
    "operator_review_status",
    "review_checks",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_fixtures_only": True,
    "local_static_samples_only": True,
    "market_action_output_allowed": False,
    "market_api_calls_allowed": False,
    "market_instruction_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "openrouter_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "polymarket_api_calls_allowed": False,
    "replay_mutates_source_artifacts_allowed": False,
    "run_codex_changes_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "timed_automation_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}

_ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/simulated_decisions/", "pm_bot/tests/", "tests/")


@dataclass(frozen=True)
class RehearsalSimulatedDecisionReplayLinksValidationResult:
    valid: bool
    errors: tuple[str, ...]


class RehearsalSimulatedDecisionReplayLinksValidationError(ValueError):
    """Raised when local rehearsal simulated decision replay links are invalid."""


def load_rehearsal_simulated_decision_replay_links(path: Path | str = SAMPLE_LINKS_PATH) -> dict[str, Any]:
    return _load_json(Path(path))


def example_rehearsal_simulated_decision_replay_links() -> dict[str, Any]:
    return deepcopy(load_rehearsal_simulated_decision_replay_links())


def load_rehearsal_simulated_decision_replay_link_inputs() -> dict[str, Any]:
    return {
        "rehearsal_artifacts": [_artifact_from_spec(spec) for spec in _REHEARSAL_ARTIFACT_SPECS],
        "simulated_decision_artifacts": [
            _artifact_from_spec(spec) for spec in _SIMULATED_DECISION_ARTIFACT_SPECS
        ],
    }


def build_rehearsal_simulated_decision_replay_links(inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    source_inputs = deepcopy(inputs) if inputs is not None else load_rehearsal_simulated_decision_replay_link_inputs()
    rehearsal_artifacts = list(source_inputs["rehearsal_artifacts"])
    simulated_decision_artifacts = list(source_inputs["simulated_decision_artifacts"])
    links = _build_link_rows(rehearsal_artifacts, simulated_decision_artifacts)
    validation_command_records = _build_validation_command_records()

    core = {
        "contract_version": LINKS_CONTRACT_VERSION,
        "created_at": "2026-05-09T10:30:00Z",
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
            "Confirm each rehearsal artifact reference resolves to the fixed local fixture or document.",
            "Confirm each simulated decision replay record identifier exists in the named static local sample.",
            "Confirm linked rows remain descriptive and pending operator review before any later use.",
            "Confirm validation output is captured before any later readiness status change.",
        ],
        "rehearsal_artifacts": rehearsal_artifacts,
        "required_validation_commands": list(REQUIRED_VALIDATION_COMMANDS),
        "run_mode": LINKS_RUN_MODE,
        "safety_boundaries": deepcopy(EXPECTED_SAFETY_BOUNDARIES),
        "simulated_decision_artifacts": simulated_decision_artifacts,
        "simulated_decision_replay_links": links,
        "task_id": TASK_ID,
        "validation_command_records": validation_command_records,
        "warnings": [],
    }
    local_references = set(_collect_values_for_key(core, "local_reference"))
    core["summary_counts"] = {
        "link_fields": len(core["link_fields"]),
        "local_references": len(local_references),
        "operator_review_steps": len(core["operator_review_steps"]),
        "rehearsal_artifacts": len(rehearsal_artifacts),
        "rehearsal_record_links": sum(len(link["rehearsal_record_ids"]) for link in links),
        "required_validation_commands": len(core["required_validation_commands"]),
        "review_checks": sum(len(link["review_checks"]) for link in links),
        "simulated_decision_artifacts": len(simulated_decision_artifacts),
        "simulated_decision_record_links": sum(
            len(record_ids)
            for link in links
            for record_ids in link["simulated_decision_record_ids"].values()
        ),
        "simulated_decision_replay_links": len(links),
        "validation_command_records": len(validation_command_records),
        "warnings": len(core["warnings"]),
    }

    link_set = {"build_id": f"{LINK_SET_ID}-{_stable_digest(core)[:12]}", **core}
    validation = validate_rehearsal_simulated_decision_replay_links(link_set)
    if not validation.valid:
        raise RehearsalSimulatedDecisionReplayLinksValidationError("; ".join(validation.errors))
    return link_set


def validate_rehearsal_simulated_decision_replay_links(
    link_set: Any,
) -> RehearsalSimulatedDecisionReplayLinksValidationResult:
    errors: list[str] = []
    if not isinstance(link_set, dict):
        return RehearsalSimulatedDecisionReplayLinksValidationResult(False, ("link set must be an object",))

    required = (
        "build_id",
        "contract_version",
        "created_at",
        "link_fields",
        "link_set_id",
        "local_only",
        "operator_review",
        "operator_review_required",
        "operator_review_steps",
        "rehearsal_artifacts",
        "required_validation_commands",
        "run_mode",
        "safety_boundaries",
        "simulated_decision_artifacts",
        "simulated_decision_replay_links",
        "summary_counts",
        "task_id",
        "validation_command_records",
        "warnings",
    )
    _require_exact_fields(link_set, required, "$", errors)
    _require_value(link_set, "contract_version", LINKS_CONTRACT_VERSION, "$.contract_version", errors)
    _require_value(link_set, "link_set_id", LINK_SET_ID, "$.link_set_id", errors)
    _require_value(link_set, "local_only", True, "$.local_only", errors)
    _require_value(link_set, "operator_review_required", True, "$.operator_review_required", errors)
    _require_value(link_set, "run_mode", LINKS_RUN_MODE, "$.run_mode", errors)
    _require_value(link_set, "task_id", TASK_ID, "$.task_id", errors)
    _validate_operator_review(link_set.get("operator_review"), errors)
    _validate_string_array(link_set.get("operator_review_steps"), "$.operator_review_steps", errors)
    _validate_string_array(link_set.get("required_validation_commands"), "$.required_validation_commands", errors)
    _validate_string_array(link_set.get("warnings"), "$.warnings", errors)
    if link_set.get("required_validation_commands") != list(REQUIRED_VALIDATION_COMMANDS):
        errors.append("$.required_validation_commands must match the required local validation command list")
    if link_set.get("safety_boundaries") != EXPECTED_SAFETY_BOUNDARIES:
        errors.append("$.safety_boundaries must match the closed local-only safety boundary contract")
    if link_set.get("link_fields") != list(EXPECTED_LINK_FIELDS):
        errors.append("$.link_fields must match the fixed link row field list")

    _validate_artifacts(link_set.get("rehearsal_artifacts"), "$.rehearsal_artifacts", errors)
    _validate_artifacts(link_set.get("simulated_decision_artifacts"), "$.simulated_decision_artifacts", errors)
    _validate_link_rows(link_set, errors)
    _validate_validation_command_records(link_set.get("validation_command_records"), errors)
    _validate_summary_counts(link_set, errors)

    return RehearsalSimulatedDecisionReplayLinksValidationResult(not errors, tuple(errors))


def build_operator_report(link_set: dict[str, Any]) -> str:
    validation = validate_rehearsal_simulated_decision_replay_links(link_set)
    if not validation.valid:
        raise RehearsalSimulatedDecisionReplayLinksValidationError("; ".join(validation.errors))

    lines = [
        "# PMBOT Rehearsal Simulated Decision Replay Links",
        "",
        f"Task: `{link_set['task_id']}`",
        f"Link set: `{link_set['link_set_id']}`",
        f"Build: `{link_set['build_id']}`",
        f"Run mode: `{link_set['run_mode']}`",
        f"Operator review: `{link_set['operator_review']['status']}`",
        "",
        "## Summary Counts",
    ]
    for key, value in link_set["summary_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Replay Links"])
    for row in link_set["simulated_decision_replay_links"]:
        lines.append(
            "- "
            f"{row['link_id']} | rehearsal artifacts: {len(row['rehearsal_artifact_ids'])} | "
            f"simulated decision artifacts: {len(row['simulated_decision_artifact_ids'])} | "
            f"review: {row['operator_review_status']}"
        )
    lines.extend(["", "## Local References"])
    for artifact in link_set["rehearsal_artifacts"] + link_set["simulated_decision_artifacts"]:
        lines.append(
            "- "
            f"{artifact['artifact_id']}: `{artifact['local_reference']}` | "
            f"records: {artifact['record_count']} | present: {artifact['present']}"
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "- Local files, local fixtures, and static samples only.",
            "- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, worker, scheduler, or browser calls.",
            "- Descriptive replay link record only.",
            "- Not execution approval and not runtime input.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local PMBOT rehearsal simulated decision replay links.")
    parser.add_argument("--output-links", required=True, type=Path)
    parser.add_argument("--output-report", required=True, type=Path)
    args = parser.parse_args(argv)

    links = build_rehearsal_simulated_decision_replay_links()
    report = build_operator_report(links)
    args.output_links.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_links.write_text(json.dumps(links, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_report.write_text(report, encoding="utf-8")
    return 0


_REHEARSAL_ARTIFACT_SPECS = (
    {
        "artifact_id": "rehearsal_validation_replay_packet_fixture",
        "artifact_role": "rehearsal_validation_replay_packet",
        "artifact_type": "json_fixture",
        "contract_version": "pmbot_rehearsal_validation_replay_packet.v1",
        "local_reference": VALIDATION_REPLAY_PACKET_PATH,
        "record_collection": "replay_records",
        "record_id_field": "record_id",
    },
    {
        "artifact_id": "rehearsal_ci_safe_validation_runner_fixture",
        "artifact_role": "rehearsal_ci_safe_validation_runner",
        "artifact_type": "json_fixture",
        "contract_version": "pmbot_rehearsal_ci_safe_validation_runner.v1",
        "local_reference": CI_SAFE_VALIDATION_RUNNER_PATH,
        "record_collection": "runner_targets",
        "record_id_field": "target_id",
    },
    {
        "artifact_id": "rehearsal_acceptance_report_document",
        "artifact_role": "rehearsal_acceptance_report",
        "artifact_type": "markdown_document",
        "contract_version": "pmbot_rehearsal_acceptance_report.v1",
        "local_reference": REHEARSAL_ACCEPTANCE_REPORT_DOC_PATH,
        "record_ids": ["PMBOT-REHEARSAL-013-REHEARSAL-ACCEPTANCE-REPORT-LOCAL-ONLY.document"],
    },
    {
        "artifact_id": "rehearsal_source_quality_links_document",
        "artifact_role": "rehearsal_source_quality_links",
        "artifact_type": "markdown_document",
        "contract_version": "pmbot_rehearsal_source_quality_links.v1",
        "local_reference": REHEARSAL_SOURCE_QUALITY_LINKS_DOC_PATH,
        "record_ids": ["PMBOT-REHEARSAL-014-REHEARSAL-SOURCE-QUALITY-LINKS-LOCAL-ONLY.document"],
    },
    {
        "artifact_id": "rehearsal_paperlive_accounting_links_document",
        "artifact_role": "rehearsal_paperlive_accounting_links",
        "artifact_type": "markdown_document",
        "contract_version": "pmbot_rehearsal_paperlive_accounting_links.v1",
        "local_reference": REHEARSAL_PAPERLIVE_ACCOUNTING_LINKS_DOC_PATH,
        "record_ids": ["PMBOT-REHEARSAL-015-REHEARSAL-PAPERLIVE-ACCOUNTING-LINKS-LOCAL-ONLY.document"],
    },
)

_SIMULATED_DECISION_ARTIFACT_SPECS = (
    {
        "artifact_id": "simulated_decision_packet_sample",
        "artifact_role": "simulated_decision_packet",
        "artifact_type": "json_sample",
        "contract_version": "pmbot_simulated_decision_packet.v1",
        "local_reference": SIMULATED_DECISION_PACKET_PATH,
        "root_id_field": "packet_id",
        "record_collections": (("record_sections", "section_id"),),
    },
    {
        "artifact_id": "simulated_decision_audit_ledger_sample",
        "artifact_role": "simulated_decision_audit_ledger",
        "artifact_type": "json_sample",
        "contract_version": "pmbot_simulated_decision_audit_ledger.v1",
        "local_reference": SIMULATED_DECISION_AUDIT_LEDGER_PATH,
        "root_id_field": "ledger_id",
        "record_collections": (
            ("audit_rows", "row_id"),
            ("record_section_rows", "row_id"),
        ),
    },
    {
        "artifact_id": "simulated_decision_replay_summary_sample",
        "artifact_role": "simulated_decision_replay_summary",
        "artifact_type": "json_sample",
        "contract_version": "pmbot_simulated_decision_replay_summary.v1",
        "local_reference": SIMULATED_DECISION_REPLAY_SUMMARY_PATH,
        "root_id_field": "summary_id",
        "record_collections": (
            ("source_ledger_rows", "row_id"),
            ("source_packet_rows", "row_id"),
            ("record_section_rows", "row_id"),
            ("replay_check_rows", "row_id"),
        ),
    },
    {
        "artifact_id": "simulated_decision_outcome_replay_links_sample",
        "artifact_role": "simulated_decision_outcome_replay_links",
        "artifact_type": "json_sample",
        "contract_version": "pmbot_simulated_decision_outcome_replay_links.v1",
        "local_reference": SIMULATED_DECISION_OUTCOME_REPLAY_LINKS_PATH,
        "root_id_field": "links_id",
        "record_collections": (
            ("source_summary_rows", "row_id"),
            ("source_packet_rows", "row_id"),
            ("outcome_artifact_rows", "row_id"),
            ("decision_to_outcome_link_rows", "row_id"),
            ("link_requirement_rows", "row_id"),
        ),
    },
)


def _artifact_from_spec(spec: dict[str, Any]) -> dict[str, Any]:
    path = _resolve_local_reference(str(spec["local_reference"]))
    data = path.read_bytes()
    record_ids = _extract_record_ids(spec, path)
    return {
        "artifact_id": spec["artifact_id"],
        "artifact_role": spec["artifact_role"],
        "artifact_type": spec["artifact_type"],
        "byte_count": len(data),
        "content_sha256": hashlib.sha256(data).hexdigest(),
        "contract_version": spec["contract_version"],
        "local_reference": spec["local_reference"],
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "present": True,
        "record_count": len(record_ids),
        "record_ids": record_ids,
    }


def _build_link_rows(
    rehearsal_artifacts: list[dict[str, Any]],
    simulated_decision_artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rehearsal_by_id = {artifact["artifact_id"]: artifact for artifact in rehearsal_artifacts}
    simulated_by_id = {artifact["artifact_id"]: artifact for artifact in simulated_decision_artifacts}
    validation_packet = rehearsal_by_id["rehearsal_validation_replay_packet_fixture"]
    ci_runner = rehearsal_by_id["rehearsal_ci_safe_validation_runner_fixture"]
    acceptance_doc = rehearsal_by_id["rehearsal_acceptance_report_document"]
    source_links_doc = rehearsal_by_id["rehearsal_source_quality_links_document"]
    accounting_links_doc = rehearsal_by_id["rehearsal_paperlive_accounting_links_document"]
    packet = simulated_by_id["simulated_decision_packet_sample"]
    audit = simulated_by_id["simulated_decision_audit_ledger_sample"]
    summary = simulated_by_id["simulated_decision_replay_summary_sample"]
    outcome_links = simulated_by_id["simulated_decision_outcome_replay_links_sample"]

    return [
        _link_row(
            link_id=f"{LINK_SET_ID}.validation_replay_to_packet_and_audit",
            rehearsal_artifacts=[validation_packet, ci_runner],
            simulated_artifacts=[packet, audit],
            link_basis="local_rehearsal_validation_records_to_simulated_decision_packet_and_audit_rows",
            replay_row_ids=[
                "simulated_decision_packet_fixture_001.packet_contract",
                "simulated_decision_packet_fixture_001.summary_counts",
                "simulated_decision_packet_fixture_001.safety_boundaries",
                "simulated_decision_packet_fixture_001.source_observation_summary",
            ],
        ),
        _link_row(
            link_id=f"{LINK_SET_ID}.operator_review_artifacts_to_replay_summary",
            rehearsal_artifacts=[acceptance_doc, source_links_doc, accounting_links_doc],
            simulated_artifacts=[summary, outcome_links],
            link_basis="local_rehearsal_operator_review_artifacts_to_simulated_decision_replay_summary_rows",
            replay_row_ids=[
                "simulated_decision_audit_ledger_fixture_001.source_audit_ledger",
                "simulated_decision_audit_ledger_fixture_001.simulated_decision_packet_fixture_001.source_packet",
                (
                    "simulated_decision_replay_summary_fixture_001.simulated_decision_packet_fixture_001."
                    "weather_outcome_reconciliation_request_fixture_001.replay_link"
                ),
            ],
        ),
    ]


def _link_row(
    *,
    link_id: str,
    rehearsal_artifacts: list[dict[str, Any]],
    simulated_artifacts: list[dict[str, Any]],
    link_basis: str,
    replay_row_ids: list[str],
) -> dict[str, Any]:
    return {
        "link_id": link_id,
        "link_state": LINK_STATE,
        "link_basis": link_basis,
        "rehearsal_artifact_ids": [artifact["artifact_id"] for artifact in rehearsal_artifacts],
        "rehearsal_record_ids": {
            artifact["artifact_id"]: artifact["record_ids"] for artifact in rehearsal_artifacts
        },
        "simulated_decision_artifact_ids": [artifact["artifact_id"] for artifact in simulated_artifacts],
        "simulated_decision_record_ids": {
            artifact["artifact_id"]: artifact["record_ids"] for artifact in simulated_artifacts
        },
        "replay_record_row_ids": replay_row_ids,
        "local_reference_pairs": [
            {
                "rehearsal_artifact_id": rehearsal_artifact["artifact_id"],
                "rehearsal_local_reference": rehearsal_artifact["local_reference"],
                "simulated_decision_artifact_id": simulated_artifact["artifact_id"],
                "simulated_decision_local_reference": simulated_artifact["local_reference"],
            }
            for rehearsal_artifact in rehearsal_artifacts
            for simulated_artifact in simulated_artifacts
        ],
        "value_policy": "record_identifiers_only_values_remain_in_local_artifacts",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "review_checks": [
            {
                "check_id": f"{link_id}.local_reference_review",
                "description": "Confirm linked local references resolve under allowed review paths.",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            },
            {
                "check_id": f"{link_id}.record_identity_review",
                "description": "Confirm rehearsal and simulated decision record identifiers exist in the named local artifacts.",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            },
            {
                "check_id": f"{link_id}.boundary_review",
                "description": "Confirm the row remains descriptive, local-only, and pending operator review.",
                "operator_review_status": OPERATOR_REVIEW_STATUS,
            },
        ],
    }


def _build_validation_command_records() -> list[dict[str, str]]:
    return [
        {
            "command_label": "python -m compileall pm_bot tests",
            "local_reference": "pm_bot/tests/test_rehearsal_simulated_decision_replay_links.py",
            "operator_review_status": OPERATOR_REVIEW_STATUS,
            "record_id": "rehearsal_simulated_decision_replay_links_001.validation.compileall",
            "status": "not_run_static_record",
        },
        {
            "command_label": "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
            "local_reference": "tests/test_codex_queue_pmbot_templates.py",
            "operator_review_status": OPERATOR_REVIEW_STATUS,
            "record_id": "rehearsal_simulated_decision_replay_links_001.validation.pytest",
            "status": "not_run_static_record",
        },
    ]


def _validate_artifacts(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path} must be a non-empty array")
        return
    required = (
        "artifact_id",
        "artifact_role",
        "artifact_type",
        "byte_count",
        "content_sha256",
        "contract_version",
        "local_reference",
        "operator_review_status",
        "present",
        "record_count",
        "record_ids",
    )
    for index, artifact in enumerate(value):
        artifact_path = f"{path}[{index}]"
        if not _require_object(artifact, artifact_path, errors):
            continue
        _require_exact_fields(artifact, required, artifact_path, errors)
        _require_value(artifact, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{artifact_path}.operator_review_status", errors)
        _require_value(artifact, "present", True, f"{artifact_path}.present", errors)
        _validate_local_reference(artifact.get("local_reference"), f"{artifact_path}.local_reference", errors)
        _validate_string_array(artifact.get("record_ids"), f"{artifact_path}.record_ids", errors)
        if isinstance(artifact.get("record_ids"), list) and artifact.get("record_count") != len(artifact["record_ids"]):
            errors.append(f"{artifact_path}.record_count must match record_ids length")
        local_reference = artifact.get("local_reference")
        if isinstance(local_reference, str) and _local_reference_exists(local_reference):
            data = _resolve_local_reference(local_reference).read_bytes()
            if artifact.get("byte_count") != len(data):
                errors.append(f"{artifact_path}.byte_count must match local bytes")
            if artifact.get("content_sha256") != hashlib.sha256(data).hexdigest():
                errors.append(f"{artifact_path}.content_sha256 must match local bytes")


def _validate_link_rows(link_set: dict[str, Any], errors: list[str]) -> None:
    links = link_set.get("simulated_decision_replay_links")
    if not isinstance(links, list) or not links:
        errors.append("$.simulated_decision_replay_links must be a non-empty array")
        return
    rehearsal_artifacts = _artifact_record_ids_by_id(link_set.get("rehearsal_artifacts"))
    simulated_artifacts = _artifact_record_ids_by_id(link_set.get("simulated_decision_artifacts"))
    required = tuple(EXPECTED_LINK_FIELDS)
    for index, link in enumerate(links):
        path = f"$.simulated_decision_replay_links[{index}]"
        if not _require_object(link, path, errors):
            continue
        _require_exact_fields(link, required, path, errors)
        _require_value(link, "link_state", LINK_STATE, f"{path}.link_state", errors)
        _require_value(link, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _validate_string_array(link.get("rehearsal_artifact_ids"), f"{path}.rehearsal_artifact_ids", errors)
        _validate_string_array(
            link.get("simulated_decision_artifact_ids"),
            f"{path}.simulated_decision_artifact_ids",
            errors,
        )
        _validate_string_array(link.get("replay_record_row_ids"), f"{path}.replay_record_row_ids", errors)
        _validate_review_checks(link.get("review_checks"), f"{path}.review_checks", errors)
        if link.get("value_policy") != "record_identifiers_only_values_remain_in_local_artifacts":
            errors.append(f"{path}.value_policy must keep values in referenced local artifacts")
        for artifact_id in link.get("rehearsal_artifact_ids", []):
            if artifact_id not in rehearsal_artifacts:
                errors.append(f"{path}.rehearsal_artifact_ids contains unknown artifact {artifact_id!r}")
        for artifact_id in link.get("simulated_decision_artifact_ids", []):
            if artifact_id not in simulated_artifacts:
                errors.append(f"{path}.simulated_decision_artifact_ids contains unknown artifact {artifact_id!r}")
        if isinstance(link.get("rehearsal_record_ids"), dict):
            for artifact_id, record_ids in link["rehearsal_record_ids"].items():
                if set(record_ids) - rehearsal_artifacts.get(artifact_id, set()):
                    errors.append(f"{path}.rehearsal_record_ids must exist in rehearsal artifacts")
        else:
            errors.append(f"{path}.rehearsal_record_ids must be an object")
        if isinstance(link.get("simulated_decision_record_ids"), dict):
            for artifact_id, record_ids in link["simulated_decision_record_ids"].items():
                if set(record_ids) - simulated_artifacts.get(artifact_id, set()):
                    errors.append(f"{path}.simulated_decision_record_ids must exist in simulated decision artifacts")
        else:
            errors.append(f"{path}.simulated_decision_record_ids must be an object")
        _validate_local_reference_pairs(link.get("local_reference_pairs"), path, errors)


def _validate_local_reference_pairs(value: Any, link_path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{link_path}.local_reference_pairs must be a non-empty array")
        return
    required = (
        "rehearsal_artifact_id",
        "rehearsal_local_reference",
        "simulated_decision_artifact_id",
        "simulated_decision_local_reference",
    )
    for index, pair in enumerate(value):
        path = f"{link_path}.local_reference_pairs[{index}]"
        if not _require_object(pair, path, errors):
            continue
        _require_exact_fields(pair, required, path, errors)
        _validate_local_reference(pair.get("rehearsal_local_reference"), f"{path}.rehearsal_local_reference", errors)
        _validate_local_reference(
            pair.get("simulated_decision_local_reference"),
            f"{path}.simulated_decision_local_reference",
            errors,
        )


def _validate_validation_command_records(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("$.validation_command_records must be an array")
        return
    for index, record in enumerate(value):
        path = f"$.validation_command_records[{index}]"
        if not _require_object(record, path, errors):
            continue
        _require_exact_fields(
            record,
            ("command_label", "local_reference", "operator_review_status", "record_id", "status"),
            path,
            errors,
        )
        _require_value(record, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _require_value(record, "status", "not_run_static_record", f"{path}.status", errors)
        _validate_local_reference(record.get("local_reference"), f"{path}.local_reference", errors)


def _validate_summary_counts(link_set: dict[str, Any], errors: list[str]) -> None:
    value = link_set.get("summary_counts")
    if not _require_object(value, "$.summary_counts", errors):
        return
    links = link_set.get("simulated_decision_replay_links") if isinstance(link_set.get("simulated_decision_replay_links"), list) else []
    local_references = set(_collect_values_for_key(link_set, "local_reference"))
    expected = {
        "link_fields": len(link_set.get("link_fields")) if isinstance(link_set.get("link_fields"), list) else 0,
        "local_references": len(local_references),
        "operator_review_steps": (
            len(link_set.get("operator_review_steps")) if isinstance(link_set.get("operator_review_steps"), list) else 0
        ),
        "rehearsal_artifacts": (
            len(link_set.get("rehearsal_artifacts")) if isinstance(link_set.get("rehearsal_artifacts"), list) else 0
        ),
        "rehearsal_record_links": sum(len(link.get("rehearsal_record_ids", {})) for link in links),
        "required_validation_commands": (
            len(link_set.get("required_validation_commands"))
            if isinstance(link_set.get("required_validation_commands"), list)
            else 0
        ),
        "review_checks": sum(len(link.get("review_checks", [])) for link in links),
        "simulated_decision_artifacts": (
            len(link_set.get("simulated_decision_artifacts"))
            if isinstance(link_set.get("simulated_decision_artifacts"), list)
            else 0
        ),
        "simulated_decision_record_links": sum(
            len(record_ids)
            for link in links
            for record_ids in link.get("simulated_decision_record_ids", {}).values()
        ),
        "simulated_decision_replay_links": len(links),
        "validation_command_records": (
            len(link_set.get("validation_command_records"))
            if isinstance(link_set.get("validation_command_records"), list)
            else 0
        ),
        "warnings": len(link_set.get("warnings")) if isinstance(link_set.get("warnings"), list) else 0,
    }
    _require_exact_fields(value, tuple(expected), "$.summary_counts", errors)
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            errors.append(f"$.summary_counts.{field} must match content: {expected_value}")


def _validate_operator_review(value: Any, errors: list[str]) -> None:
    if not _require_object(value, "$.operator_review", errors):
        return
    _require_exact_fields(value, ("reviewed_at", "reviewed_by", "status"), "$.operator_review", errors)
    _require_value(value, "status", OPERATOR_REVIEW_STATUS, "$.operator_review.status", errors)
    if value.get("reviewed_at") is not None:
        errors.append("$.operator_review.reviewed_at must be null before operator review")
    if value.get("reviewed_by") is not None:
        errors.append("$.operator_review.reviewed_by must be null before operator review")


def _validate_review_checks(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path} must be a non-empty array")
        return
    for index, check in enumerate(value):
        check_path = f"{path}[{index}]"
        if not _require_object(check, check_path, errors):
            continue
        _require_exact_fields(check, ("check_id", "description", "operator_review_status"), check_path, errors)
        _require_value(check, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{check_path}.operator_review_status", errors)


def _extract_record_ids(spec: dict[str, Any], path: Path) -> list[str]:
    if "record_ids" in spec:
        return list(spec["record_ids"])
    data = _load_json(path)
    record_ids: list[str] = []
    root_id_field = spec.get("root_id_field")
    if isinstance(root_id_field, str) and isinstance(data.get(root_id_field), str):
        record_ids.append(data[root_id_field])
    record_collection = spec.get("record_collection")
    record_id_field = spec.get("record_id_field")
    if isinstance(record_collection, str) and isinstance(record_id_field, str):
        record_ids.extend(
            item[record_id_field]
            for item in data.get(record_collection, [])
            if isinstance(item, dict) and isinstance(item.get(record_id_field), str)
        )
    for collection, id_field in spec.get("record_collections", ()):
        record_ids.extend(
            item[id_field]
            for item in data.get(collection, [])
            if isinstance(item, dict) and isinstance(item.get(id_field), str)
        )
    return sorted(dict.fromkeys(record_ids))


def _artifact_record_ids_by_id(value: Any) -> dict[str, set[str]]:
    if not isinstance(value, list):
        return {}
    return {
        artifact["artifact_id"]: set(artifact["record_ids"])
        for artifact in value
        if isinstance(artifact, dict)
        and isinstance(artifact.get("artifact_id"), str)
        and isinstance(artifact.get("record_ids"), list)
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _collect_values_for_key(value: Any, key: str) -> list[str]:
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


def _resolve_local_reference(value: str) -> Path:
    return (_WORKSPACE_ROOT / value).resolve()


def _local_reference_exists(value: str) -> bool:
    try:
        return _resolve_local_reference(value).exists()
    except OSError:
        return False


def _validate_local_reference(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{path} must be a non-empty local reference")
        return
    if "://" in value or Path(value).is_absolute() or ".." in Path(value).parts:
        errors.append(f"{path} must be a local repository-relative reference")
        return
    if not value.startswith(_ALLOWED_LOCAL_PREFIXES):
        errors.append(f"{path} must stay under PMBOT rehearsal allowed local paths")
        return
    resolved = _resolve_local_reference(value)
    try:
        resolved.relative_to(_WORKSPACE_ROOT)
    except ValueError:
        errors.append(f"{path} must stay inside the local workspace")
        return
    if not resolved.exists():
        errors.append(f"{path} must point to an existing local artifact")


def _validate_string_array(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(f"{path}[{index}] must be a string")


def _require_object(value: Any, path: str, errors: list[str]) -> bool:
    if isinstance(value, dict):
        return True
    errors.append(f"{path} must be an object")
    return False


def _require_exact_fields(value: dict[str, Any], required_fields: tuple[str, ...], path: str, errors: list[str]) -> None:
    required = set(required_fields)
    present = set(value)
    missing = sorted(required - present)
    unexpected = sorted(present - required)
    if missing:
        errors.append(f"{path} missing required fields: {', '.join(missing)}")
    if unexpected:
        errors.append(f"{path} has unexpected fields: {', '.join(unexpected)}")


def _require_value(value: dict[str, Any], field: str, expected: Any, path: str, errors: list[str]) -> None:
    if value.get(field) != expected:
        errors.append(f"{path} must be {expected!r}")


if __name__ == "__main__":
    raise SystemExit(main())
