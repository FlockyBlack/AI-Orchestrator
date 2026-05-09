from __future__ import annotations

import argparse
import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pm_bot.simulated_decisions.audit_ledger import LOCAL_ONLY_SAFETY_BOUNDARIES
from pm_bot.simulated_decisions.replay_summary import (
    REPLAY_SUMMARY_CONTRACT_VERSION,
    REPLAY_SUMMARY_STATE,
    validate_simulated_decision_replay_summary,
)
from pm_bot.simulated_decisions.schema import LOCAL_RUN_MODE, OPERATOR_REVIEW_STATUS, PACKET_STATE

OUTCOME_REPLAY_LINKS_REQUEST_CONTRACT_VERSION = "pmbot_simulated_decision_outcome_replay_links_request.v1"
OUTCOME_REPLAY_LINKS_CONTRACT_VERSION = "pmbot_simulated_decision_outcome_replay_links.v1"
OUTCOME_REPLAY_LINKS_SCHEMA_ID = "pmbot_simulated_decision_outcome_replay_links_schema.v1"
OUTCOME_REPLAY_LINKS_STATE = "recorded_for_operator_review"

_PACKAGE_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _PACKAGE_DIR.parents[1]
OUTCOME_REPLAY_LINKS_SCHEMA_PATH = (
    _PACKAGE_DIR / "schemas" / "simulated_decision_outcome_replay_links.schema.v1.json"
)
SAMPLE_OUTCOME_REPLAY_LINKS_PATH = (
    _PACKAGE_DIR / "samples" / "simulated_decision_outcome_replay_links.fixture.json"
)
_ALLOWED_LOCAL_REFERENCE_PREFIXES = ("pm_bot/simulated_decisions/", "pm_bot/tests/fixtures/")
_ID_RE = re.compile(r"^[a-z0-9_.-]+$")
_UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_FORBIDDEN_OUTPUT_TOKENS = frozenset(
    {
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
        "score",
        "scoring",
        "selection",
        "sell",
        "side",
        "stake",
        "wager",
    }
)


@dataclass(frozen=True)
class SimulatedDecisionOutcomeReplayLinksValidationResult:
    valid: bool
    errors: tuple[str, ...]


class SimulatedDecisionOutcomeReplayLinksValidationError(ValueError):
    """Raised when local simulated decision outcome replay link input is invalid."""


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


SIMULATED_DECISION_OUTCOME_REPLAY_LINKS_SCHEMA = _load_json(OUTCOME_REPLAY_LINKS_SCHEMA_PATH)
SIMULATED_DECISION_OUTCOME_REPLAY_LINKS_FIXTURE = _load_json(SAMPLE_OUTCOME_REPLAY_LINKS_PATH)


def build_simulated_decision_outcome_replay_links_schema() -> dict[str, Any]:
    """Return a detached copy of the local outcome replay links schema artifact."""

    return deepcopy(SIMULATED_DECISION_OUTCOME_REPLAY_LINKS_SCHEMA)


def example_simulated_decision_outcome_replay_links() -> dict[str, Any]:
    """Return a detached copy of the static local outcome replay links fixture."""

    return deepcopy(SIMULATED_DECISION_OUTCOME_REPLAY_LINKS_FIXTURE)


def load_outcome_replay_links_request(path: Path | str) -> dict[str, Any]:
    return _load_json(Path(path))


def validate_outcome_replay_links_request(request: Any) -> SimulatedDecisionOutcomeReplayLinksValidationResult:
    errors: list[str] = []
    if not isinstance(request, dict):
        return SimulatedDecisionOutcomeReplayLinksValidationResult(False, ("request must be an object",))

    required = (
        "contract_version",
        "links_id",
        "created_at",
        "replay_scope",
        "local_only",
        "operator_review_required",
        "source_replay_summaries",
        "outcome_artifacts",
        "link_requirements",
        "operator_review_steps",
    )
    _require_exact_fields(request, required, "$", errors)
    _require_value(
        request,
        "contract_version",
        OUTCOME_REPLAY_LINKS_REQUEST_CONTRACT_VERSION,
        "$.contract_version",
        errors,
    )
    _require_local_id(request.get("links_id"), "$.links_id", errors)
    _require_utc_timestamp(request.get("created_at"), "$.created_at", errors)
    _require_non_empty_string(request.get("replay_scope"), "$.replay_scope", errors)
    _require_value(request, "local_only", True, "$.local_only", errors)
    _require_value(request, "operator_review_required", True, "$.operator_review_required", errors)
    _validate_source_replay_summaries(request.get("source_replay_summaries"), errors)
    _validate_outcome_artifacts(request.get("outcome_artifacts"), errors)
    _validate_link_requirements(request.get("link_requirements"), errors)
    _validate_string_array(request.get("operator_review_steps"), "$.operator_review_steps", errors)

    for path in _find_forbidden_output_terms(request):
        errors.append(f"forbidden output field detected in outcome replay links request at {path}")

    return SimulatedDecisionOutcomeReplayLinksValidationResult(not errors, tuple(errors))


def build_simulated_decision_outcome_replay_links(request: dict[str, Any]) -> dict[str, Any]:
    validation = validate_outcome_replay_links_request(request)
    if not validation.valid:
        raise SimulatedDecisionOutcomeReplayLinksValidationError("; ".join(validation.errors))

    source_summaries = _load_source_replay_summaries(request)
    outcome_artifacts = _load_outcome_artifacts(request)
    build_id = (
        f"{request['links_id']}-"
        f"{_stable_digest({'request': request, 'source_summaries': source_summaries, 'outcome_artifacts': outcome_artifacts})[:12]}"
    )
    source_summary_rows = _build_source_summary_rows(source_summaries)
    source_packet_rows = _build_source_packet_rows(source_summaries)
    outcome_artifact_rows = _build_outcome_artifact_rows(outcome_artifacts)
    decision_to_outcome_link_rows = _build_decision_to_outcome_link_rows(source_summaries, outcome_artifacts)
    local_reference_rows = _build_local_reference_rows(source_summaries, outcome_artifacts)
    link_requirement_rows = _build_link_requirement_rows(request)
    warnings: list[str] = []
    errors: list[str] = []

    links = {
        "contract_version": OUTCOME_REPLAY_LINKS_CONTRACT_VERSION,
        "links_id": request["links_id"],
        "build_id": build_id,
        "created_at": request["created_at"],
        "replay_scope": request["replay_scope"],
        "run_mode": LOCAL_RUN_MODE,
        "local_only": True,
        "operator_review_required": True,
        "links_state": OUTCOME_REPLAY_LINKS_STATE,
        "source_summary_rows": source_summary_rows,
        "source_packet_rows": source_packet_rows,
        "outcome_artifact_rows": outcome_artifact_rows,
        "decision_to_outcome_link_rows": decision_to_outcome_link_rows,
        "local_reference_rows": local_reference_rows,
        "link_requirement_rows": link_requirement_rows,
        "summary_counts": {
            "source_summaries": len(source_summary_rows),
            "source_packets": len(source_packet_rows),
            "outcome_artifacts": len(outcome_artifact_rows),
            "decision_to_outcome_links": len(decision_to_outcome_link_rows),
            "local_references": len(local_reference_rows),
            "link_requirements": len(link_requirement_rows),
            "warnings": len(warnings),
            "errors": len(errors),
        },
        "operator_review": {
            "status": OPERATOR_REVIEW_STATUS,
            "reviewed_by": None,
            "reviewed_at": None,
            "notes": [],
        },
        "safety_boundaries": deepcopy(LOCAL_ONLY_SAFETY_BOUNDARIES),
        "warnings": warnings,
        "errors": errors,
    }
    output_validation = validate_simulated_decision_outcome_replay_links(links)
    if not output_validation.valid:
        raise SimulatedDecisionOutcomeReplayLinksValidationError("; ".join(output_validation.errors))
    return links


def validate_simulated_decision_outcome_replay_links(
    links: Any,
) -> SimulatedDecisionOutcomeReplayLinksValidationResult:
    errors: list[str] = []
    if not isinstance(links, dict):
        return SimulatedDecisionOutcomeReplayLinksValidationResult(False, ("links must be an object",))

    required = tuple(SIMULATED_DECISION_OUTCOME_REPLAY_LINKS_SCHEMA["required_fields"])
    _require_exact_fields(links, required, "$", errors)
    _require_value(links, "contract_version", OUTCOME_REPLAY_LINKS_CONTRACT_VERSION, "$.contract_version", errors)
    _require_local_id(links.get("links_id"), "$.links_id", errors)
    _require_non_empty_string(links.get("build_id"), "$.build_id", errors)
    _require_utc_timestamp(links.get("created_at"), "$.created_at", errors)
    _require_non_empty_string(links.get("replay_scope"), "$.replay_scope", errors)
    _require_value(links, "run_mode", LOCAL_RUN_MODE, "$.run_mode", errors)
    _require_value(links, "local_only", True, "$.local_only", errors)
    _require_value(links, "operator_review_required", True, "$.operator_review_required", errors)
    _require_value(links, "links_state", OUTCOME_REPLAY_LINKS_STATE, "$.links_state", errors)

    _validate_source_summary_rows(links.get("source_summary_rows"), errors)
    _validate_source_packet_rows(links.get("source_packet_rows"), errors)
    _validate_outcome_artifact_rows(links.get("outcome_artifact_rows"), errors)
    _validate_link_rows(links.get("decision_to_outcome_link_rows"), errors)
    _validate_reference_rows(links.get("local_reference_rows"), errors)
    _validate_status_rows(links.get("link_requirement_rows"), "$.link_requirement_rows", errors)
    _validate_summary_counts(links, errors)
    _validate_operator_review(links.get("operator_review"), errors)
    _validate_safety_boundaries(links.get("safety_boundaries"), errors)
    _validate_string_array(links.get("warnings"), "$.warnings", errors)
    _validate_string_array(links.get("errors"), "$.errors", errors)

    for path in _find_forbidden_output_terms(links):
        errors.append(f"forbidden output field detected in outcome replay links at {path}")

    return SimulatedDecisionOutcomeReplayLinksValidationResult(not errors, tuple(errors))


def build_operator_report(links: dict[str, Any]) -> str:
    validation = validate_simulated_decision_outcome_replay_links(links)
    if not validation.valid:
        raise SimulatedDecisionOutcomeReplayLinksValidationError("; ".join(validation.errors))

    lines = [
        "# PMBOT Simulated Decision To Outcome Replay Links",
        "",
        f"Links: `{links['links_id']}`",
        f"Build: `{links['build_id']}`",
        f"Run mode: `{links['run_mode']}`",
        f"Operator review: `{links['operator_review']['status']}`",
        "",
        "## Summary Counts",
    ]
    for key, value in links["summary_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Link Rows"])
    for row in links["decision_to_outcome_link_rows"]:
        lines.append(
            "- "
            f"{row['source_packet_id']} -> {row['outcome_artifact_id']} | "
            f"records: {len(row['outcome_record_ids'])} | review: {row['operator_review_status']}"
        )
    lines.extend(["", "## Local References"])
    for row in links["local_reference_rows"]:
        lines.append(f"- {row['reference_role']}: `{row['local_reference']}` | exists: {row['reference_exists']}")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "- Local fixture/static input only.",
            "- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, worker, scheduler, or browser calls.",
            "- Descriptive replay-link record only; not runtime input or execution approval.",
            "- Leaves any final outcome record outside this artifact.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local PMBOT simulated decision outcome replay links.")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--output-links", required=True, type=Path)
    parser.add_argument("--output-report", required=True, type=Path)
    args = parser.parse_args(argv)

    request = load_outcome_replay_links_request(args.request)
    links = build_simulated_decision_outcome_replay_links(request)
    report = build_operator_report(links)

    args.output_links.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_links.write_text(json.dumps(links, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_report.write_text(report, encoding="utf-8")
    return 0


def _load_source_replay_summaries(request: dict[str, Any]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for index, source in enumerate(request["source_replay_summaries"]):
        summary_path = (_WORKSPACE_ROOT / source["local_reference"]).resolve()
        summary = _load_json(summary_path)
        validation = validate_simulated_decision_replay_summary(summary)
        if not validation.valid:
            raise SimulatedDecisionOutcomeReplayLinksValidationError(
                f"source_replay_summaries[{index}] summary failed validation: {'; '.join(validation.errors)}"
            )
        if summary["summary_id"] != source["source_summary_id"]:
            raise SimulatedDecisionOutcomeReplayLinksValidationError(
                f"source_replay_summaries[{index}].source_summary_id must match the local replay summary id"
            )
        summaries.append({"request_source": deepcopy(source), "summary": summary})
    return summaries


def _load_outcome_artifacts(request: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for index, source in enumerate(request["outcome_artifacts"]):
        artifact_path = (_WORKSPACE_ROOT / source["local_reference"]).resolve()
        artifact = _load_json(artifact_path)
        if artifact.get("contract_version") != source["expected_contract_version"]:
            raise SimulatedDecisionOutcomeReplayLinksValidationError(
                f"outcome_artifacts[{index}].expected_contract_version must match the local artifact contract"
            )
        artifacts.append({"request_source": deepcopy(source), "artifact": artifact})
    return artifacts


def _build_source_summary_rows(source_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded in source_summaries:
        source = loaded["request_source"]
        summary = loaded["summary"]
        rows.append(
            {
                "row_id": f"{summary['summary_id']}.source_replay_summary",
                "source_summary_id": source["source_summary_id"],
                "source_summary_label": source["source_summary_label"],
                "local_reference": source["local_reference"],
                "artifact_loaded": True,
                "contract_version": summary["contract_version"],
                "summary_state": summary["summary_state"],
                "source_packet_count": summary["summary_counts"]["source_packets"],
                "record_section_row_count": summary["summary_counts"]["record_section_rows"],
                "local_reference_count": summary["summary_counts"]["local_references"],
                "replay_check_count": summary["summary_counts"]["replay_checks"],
                "warning_count": len(summary["warnings"]),
                "error_count": len(summary["errors"]),
                "operator_review_status": source["operator_review_status"],
                "row_state": OUTCOME_REPLAY_LINKS_STATE,
            }
        )
    return rows


def _build_source_packet_rows(source_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded in source_summaries:
        summary = loaded["summary"]
        for packet_row in summary["source_packet_rows"]:
            rows.append(
                {
                    "row_id": f"{summary['summary_id']}.{packet_row['source_packet_id']}.source_packet",
                    "source_summary_id": summary["summary_id"],
                    "source_ledger_id": packet_row["source_ledger_id"],
                    "source_packet_id": packet_row["source_packet_id"],
                    "source_packet_label": packet_row["source_packet_label"],
                    "local_reference": packet_row["local_reference"],
                    "packet_state": packet_row["packet_state"],
                    "record_section_count": packet_row["record_section_count"],
                    "observation_count": packet_row["observation_count"],
                    "operator_review_status": packet_row["operator_review_status"],
                    "row_state": OUTCOME_REPLAY_LINKS_STATE,
                }
            )
    return rows


def _build_outcome_artifact_rows(outcome_artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded in outcome_artifacts:
        source = loaded["request_source"]
        artifact = loaded["artifact"]
        rows.append(
            {
                "row_id": f"{source['outcome_artifact_id']}.outcome_artifact",
                "outcome_artifact_id": source["outcome_artifact_id"],
                "outcome_artifact_label": source["outcome_artifact_label"],
                "artifact_role": source["artifact_role"],
                "local_reference": source["local_reference"],
                "artifact_loaded": True,
                "contract_version": artifact["contract_version"],
                "observation_record_count": _len_if_list(artifact.get("observation_records")),
                "outcome_review_count": _len_if_list(artifact.get("outcome_reviews")),
                "warning_count": _len_if_list(artifact.get("warnings")),
                "error_count": _len_if_list(artifact.get("errors")),
                "operator_review_status": source["operator_review_status"],
                "row_state": OUTCOME_REPLAY_LINKS_STATE,
            }
        )
    return rows


def _build_decision_to_outcome_link_rows(
    source_summaries: list[dict[str, Any]],
    outcome_artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded_summary in source_summaries:
        summary = loaded_summary["summary"]
        section_rows_by_packet = _section_rows_by_packet(summary)
        for packet_row in summary["source_packet_rows"]:
            section_rows = section_rows_by_packet.get(packet_row["source_packet_id"], [])
            section_ids = sorted(row["section_id"] for row in section_rows)
            source_artifact_ids = sorted(
                {
                    artifact_id
                    for row in section_rows
                    for artifact_id in row.get("source_artifact_ids", [])
                }
            )
            for loaded_artifact in outcome_artifacts:
                source = loaded_artifact["request_source"]
                artifact = loaded_artifact["artifact"]
                rows.append(
                    {
                        "row_id": (
                            f"{summary['summary_id']}.{packet_row['source_packet_id']}."
                            f"{source['outcome_artifact_id']}.replay_link"
                        ),
                        "source_summary_id": summary["summary_id"],
                        "source_packet_id": packet_row["source_packet_id"],
                        "source_packet_label": packet_row["source_packet_label"],
                        "decision_record_reference": packet_row["local_reference"],
                        "outcome_artifact_id": source["outcome_artifact_id"],
                        "outcome_artifact_label": source["outcome_artifact_label"],
                        "outcome_artifact_reference": source["local_reference"],
                        "link_basis": source["link_basis"],
                        "linked_section_ids": section_ids,
                        "source_artifact_ids": source_artifact_ids,
                        "outcome_record_ids": _record_ids_from_outcome_artifact(artifact),
                        "outcome_review_ids": _review_ids_from_outcome_artifact(artifact),
                        "operator_review_status": OPERATOR_REVIEW_STATUS,
                        "row_state": OUTCOME_REPLAY_LINKS_STATE,
                    }
                )
    return rows


def _build_local_reference_rows(
    source_summaries: list[dict[str, Any]],
    outcome_artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded in source_summaries:
        source = loaded["request_source"]
        rows.append(
            {
                "row_id": f"{source['source_summary_id']}.source_replay_summary",
                "reference_role": "source_replay_summary",
                "local_reference": source["local_reference"],
                "reference_exists": (_WORKSPACE_ROOT / source["local_reference"]).resolve().exists(),
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "row_state": OUTCOME_REPLAY_LINKS_STATE,
            }
        )
    for loaded in outcome_artifacts:
        source = loaded["request_source"]
        rows.append(
            {
                "row_id": f"{source['outcome_artifact_id']}.outcome_artifact",
                "reference_role": source["artifact_role"],
                "local_reference": source["local_reference"],
                "reference_exists": (_WORKSPACE_ROOT / source["local_reference"]).resolve().exists(),
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "row_state": OUTCOME_REPLAY_LINKS_STATE,
            }
        )
    return rows


def _build_link_requirement_rows(request: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": requirement["requirement_id"],
            "requirement_id": requirement["requirement_id"],
            "description": requirement["description"],
            "operator_review_status": requirement["operator_review_status"],
            "row_state": OUTCOME_REPLAY_LINKS_STATE,
        }
        for requirement in request["link_requirements"]
    ]


def _validate_source_replay_summaries(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("$.source_replay_summaries must be a non-empty array")
        return
    required = ("source_summary_id", "source_summary_label", "local_reference", "operator_review_status")
    seen: set[str] = set()
    for index, source in enumerate(value):
        path = f"$.source_replay_summaries[{index}]"
        if not _require_object(source, path, errors):
            continue
        _require_exact_fields(source, required, path, errors)
        _require_local_id(source.get("source_summary_id"), f"{path}.source_summary_id", errors)
        _require_non_empty_string(source.get("source_summary_label"), f"{path}.source_summary_label", errors)
        _require_value(source, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _validate_local_reference(source.get("local_reference"), f"{path}.local_reference", errors)
        if isinstance(source.get("source_summary_id"), str):
            if source["source_summary_id"] in seen:
                errors.append(f"{path}.source_summary_id must be unique")
            seen.add(source["source_summary_id"])


def _validate_outcome_artifacts(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("$.outcome_artifacts must be a non-empty array")
        return
    required = (
        "outcome_artifact_id",
        "outcome_artifact_label",
        "artifact_role",
        "local_reference",
        "expected_contract_version",
        "link_basis",
        "operator_review_status",
    )
    seen: set[str] = set()
    for index, source in enumerate(value):
        path = f"$.outcome_artifacts[{index}]"
        if not _require_object(source, path, errors):
            continue
        _require_exact_fields(source, required, path, errors)
        _require_local_id(source.get("outcome_artifact_id"), f"{path}.outcome_artifact_id", errors)
        _require_non_empty_string(source.get("outcome_artifact_label"), f"{path}.outcome_artifact_label", errors)
        _require_local_id(source.get("artifact_role"), f"{path}.artifact_role", errors)
        _require_non_empty_string(source.get("expected_contract_version"), f"{path}.expected_contract_version", errors)
        _require_non_empty_string(source.get("link_basis"), f"{path}.link_basis", errors)
        _require_value(source, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _validate_local_reference(source.get("local_reference"), f"{path}.local_reference", errors)
        if isinstance(source.get("outcome_artifact_id"), str):
            if source["outcome_artifact_id"] in seen:
                errors.append(f"{path}.outcome_artifact_id must be unique")
            seen.add(source["outcome_artifact_id"])


def _validate_link_requirements(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("$.link_requirements must be a non-empty array")
        return
    required = ("requirement_id", "description", "operator_review_status")
    seen: set[str] = set()
    for index, requirement in enumerate(value):
        path = f"$.link_requirements[{index}]"
        if not _require_object(requirement, path, errors):
            continue
        _require_exact_fields(requirement, required, path, errors)
        _require_local_id(requirement.get("requirement_id"), f"{path}.requirement_id", errors)
        _require_non_empty_string(requirement.get("description"), f"{path}.description", errors)
        _require_value(
            requirement,
            "operator_review_status",
            OPERATOR_REVIEW_STATUS,
            f"{path}.operator_review_status",
            errors,
        )
        if isinstance(requirement.get("requirement_id"), str):
            if requirement["requirement_id"] in seen:
                errors.append(f"{path}.requirement_id must be unique")
            seen.add(requirement["requirement_id"])


def _validate_source_summary_rows(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("$.source_summary_rows must be an array")
        return
    for index, row in enumerate(value):
        path = f"$.source_summary_rows[{index}]"
        if not _require_object(row, path, errors):
            continue
        _require_value(row, "contract_version", REPLAY_SUMMARY_CONTRACT_VERSION, f"{path}.contract_version", errors)
        _require_value(row, "summary_state", REPLAY_SUMMARY_STATE, f"{path}.summary_state", errors)
        _require_value(row, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _require_value(row, "row_state", OUTCOME_REPLAY_LINKS_STATE, f"{path}.row_state", errors)
        _validate_local_reference(row.get("local_reference"), f"{path}.local_reference", errors)


def _validate_source_packet_rows(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("$.source_packet_rows must be an array")
        return
    for index, row in enumerate(value):
        path = f"$.source_packet_rows[{index}]"
        if not _require_object(row, path, errors):
            continue
        _require_value(row, "packet_state", PACKET_STATE, f"{path}.packet_state", errors)
        _require_value(row, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _require_value(row, "row_state", OUTCOME_REPLAY_LINKS_STATE, f"{path}.row_state", errors)
        _validate_local_reference(row.get("local_reference"), f"{path}.local_reference", errors)


def _validate_outcome_artifact_rows(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("$.outcome_artifact_rows must be an array")
        return
    for index, row in enumerate(value):
        path = f"$.outcome_artifact_rows[{index}]"
        if not _require_object(row, path, errors):
            continue
        _require_value(row, "artifact_loaded", True, f"{path}.artifact_loaded", errors)
        _require_value(row, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _require_value(row, "row_state", OUTCOME_REPLAY_LINKS_STATE, f"{path}.row_state", errors)
        _validate_local_reference(row.get("local_reference"), f"{path}.local_reference", errors)


def _validate_link_rows(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("$.decision_to_outcome_link_rows must be an array")
        return
    for index, row in enumerate(value):
        path = f"$.decision_to_outcome_link_rows[{index}]"
        if not _require_object(row, path, errors):
            continue
        _require_value(row, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _require_value(row, "row_state", OUTCOME_REPLAY_LINKS_STATE, f"{path}.row_state", errors)
        _validate_local_reference(row.get("decision_record_reference"), f"{path}.decision_record_reference", errors)
        _validate_local_reference(row.get("outcome_artifact_reference"), f"{path}.outcome_artifact_reference", errors)
        _validate_string_array(row.get("linked_section_ids"), f"{path}.linked_section_ids", errors)
        _validate_string_array(row.get("source_artifact_ids"), f"{path}.source_artifact_ids", errors)
        _validate_string_array(row.get("outcome_record_ids"), f"{path}.outcome_record_ids", errors)
        _validate_string_array(row.get("outcome_review_ids"), f"{path}.outcome_review_ids", errors)


def _validate_reference_rows(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("$.local_reference_rows must be an array")
        return
    for index, row in enumerate(value):
        path = f"$.local_reference_rows[{index}]"
        if not _require_object(row, path, errors):
            continue
        _require_value(row, "reference_exists", True, f"{path}.reference_exists", errors)
        _require_value(row, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _require_value(row, "row_state", OUTCOME_REPLAY_LINKS_STATE, f"{path}.row_state", errors)
        _validate_local_reference(row.get("local_reference"), f"{path}.local_reference", errors)


def _validate_status_rows(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return
    for index, row in enumerate(value):
        row_path = f"{path}[{index}]"
        if not _require_object(row, row_path, errors):
            continue
        _require_value(row, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{row_path}.operator_review_status", errors)
        _require_value(row, "row_state", OUTCOME_REPLAY_LINKS_STATE, f"{row_path}.row_state", errors)


def _validate_summary_counts(links: dict[str, Any], errors: list[str]) -> None:
    value = links.get("summary_counts")
    if not _require_object(value, "$.summary_counts", errors):
        return
    expected = {
        "source_summaries": (
            len(links.get("source_summary_rows")) if isinstance(links.get("source_summary_rows"), list) else 0
        ),
        "source_packets": (
            len(links.get("source_packet_rows")) if isinstance(links.get("source_packet_rows"), list) else 0
        ),
        "outcome_artifacts": (
            len(links.get("outcome_artifact_rows")) if isinstance(links.get("outcome_artifact_rows"), list) else 0
        ),
        "decision_to_outcome_links": (
            len(links.get("decision_to_outcome_link_rows"))
            if isinstance(links.get("decision_to_outcome_link_rows"), list)
            else 0
        ),
        "local_references": (
            len(links.get("local_reference_rows")) if isinstance(links.get("local_reference_rows"), list) else 0
        ),
        "link_requirements": (
            len(links.get("link_requirement_rows")) if isinstance(links.get("link_requirement_rows"), list) else 0
        ),
        "warnings": len(links.get("warnings")) if isinstance(links.get("warnings"), list) else 0,
        "errors": len(links.get("errors")) if isinstance(links.get("errors"), list) else 0,
    }
    _require_exact_fields(value, tuple(expected), "$.summary_counts", errors)
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            errors.append(f"$.summary_counts.{field} must match outcome replay links content: {expected_value}")


def _validate_operator_review(value: Any, errors: list[str]) -> None:
    if not _require_object(value, "$.operator_review", errors):
        return
    required = ("status", "reviewed_by", "reviewed_at", "notes")
    _require_exact_fields(value, required, "$.operator_review", errors)
    _require_value(value, "status", OPERATOR_REVIEW_STATUS, "$.operator_review.status", errors)
    if value.get("reviewed_by") is not None:
        errors.append("$.operator_review.reviewed_by must be null before operator review")
    if value.get("reviewed_at") is not None:
        errors.append("$.operator_review.reviewed_at must be null before operator review")
    _validate_string_array(value.get("notes"), "$.operator_review.notes", errors)


def _validate_safety_boundaries(value: Any, errors: list[str]) -> None:
    if value != LOCAL_ONLY_SAFETY_BOUNDARIES:
        errors.append("$.safety_boundaries must match the closed local-only safety boundary contract")


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


def _require_non_empty_string(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{path} must be a non-empty string")


def _require_local_id(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        errors.append(f"{path} must be a lowercase local identifier")


def _require_utc_timestamp(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not _UTC_TIMESTAMP_RE.fullmatch(value):
        errors.append(f"{path} must be a UTC timestamp formatted as YYYY-MM-DDTHH:MM:SSZ")


def _validate_string_array(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(f"{path}[{index}] must be a string")


def _validate_local_reference(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{path} must be a non-empty local reference")
        return
    if "://" in value or Path(value).is_absolute() or ".." in Path(value).parts:
        errors.append(f"{path} must be a local repository-relative reference")
        return
    if not value.startswith(_ALLOWED_LOCAL_REFERENCE_PREFIXES):
        errors.append(f"{path} must stay under simulated decision allowed local paths")
        return

    resolved = (_WORKSPACE_ROOT / value).resolve()
    try:
        resolved.relative_to(_WORKSPACE_ROOT)
    except ValueError:
        errors.append(f"{path} must stay inside the local workspace")
        return
    if not resolved.exists():
        errors.append(f"{path} must point to an existing local artifact")


def _stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _find_forbidden_output_terms(value: Any, path: str = "$") -> tuple[str, ...]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_forbidden_token(str(key)):
                hits.append(key_path)
            hits.extend(_find_forbidden_output_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_forbidden_output_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_forbidden_token(value):
        hits.append(path)
    return tuple(hits)


def _has_forbidden_token(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & _FORBIDDEN_OUTPUT_TOKENS)


def _section_rows_by_packet(summary: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows_by_packet: dict[str, list[dict[str, Any]]] = {}
    for row in summary["record_section_rows"]:
        rows_by_packet.setdefault(row["source_packet_id"], []).append(row)
    return rows_by_packet


def _record_ids_from_outcome_artifact(artifact: dict[str, Any]) -> list[str]:
    records = artifact.get("observation_records")
    if not isinstance(records, list):
        return []
    return sorted(record["record_id"] for record in records if isinstance(record, dict) and isinstance(record.get("record_id"), str))


def _review_ids_from_outcome_artifact(artifact: dict[str, Any]) -> list[str]:
    reviews = artifact.get("outcome_reviews")
    if not isinstance(reviews, list):
        return []
    return sorted(review["outcome_id"] for review in reviews if isinstance(review, dict) and isinstance(review.get("outcome_id"), str))


def _len_if_list(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


if __name__ == "__main__":
    raise SystemExit(main())
