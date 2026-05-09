from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SIMULATED_DECISION_PACKET_CONTRACT_VERSION = "pmbot_simulated_decision_packet.v1"
SIMULATED_DECISION_PACKET_SCHEMA_ID = "pmbot_simulated_decision_packet_schema.v1"
LOCAL_RUN_MODE = "offline_recordkeeping"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
PACKET_STATE = "recorded_for_operator_review"

_PACKAGE_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _PACKAGE_DIR.parents[1]
SCHEMA_PATH = _PACKAGE_DIR / "schemas" / "simulated_decision_packet.schema.v1.json"
SAMPLE_PACKET_PATH = _PACKAGE_DIR / "samples" / "simulated_decision_packet.fixture.json"
_ALLOWED_LOCAL_REFERENCE_PREFIXES = ("pm_bot/tests/fixtures/", "pm_bot/simulated_decisions/")
_PACKET_ID_RE = re.compile(r"^[a-z0-9_.-]+$")
_UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_FORBIDDEN_DECISION_TOKENS = frozenset(
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
class SimulatedDecisionPacketValidationResult:
    valid: bool
    errors: tuple[str, ...]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


SIMULATED_DECISION_PACKET_SCHEMA = _load_json(SCHEMA_PATH)
SIMULATED_DECISION_PACKET_FIXTURE = _load_json(SAMPLE_PACKET_PATH)


def build_simulated_decision_packet_schema() -> dict[str, Any]:
    """Return a detached copy of the local packet schema artifact."""

    return deepcopy(SIMULATED_DECISION_PACKET_SCHEMA)


def example_simulated_decision_packet() -> dict[str, Any]:
    """Return a detached copy of the static local packet fixture."""

    return deepcopy(SIMULATED_DECISION_PACKET_FIXTURE)


def required_packet_fields() -> tuple[str, ...]:
    return tuple(SIMULATED_DECISION_PACKET_SCHEMA["required_fields"])


def validate_simulated_decision_packet(packet: Any) -> SimulatedDecisionPacketValidationResult:
    """Validate a local simulated decision packet without producing market guidance."""

    errors: list[str] = []
    if not isinstance(packet, dict):
        return SimulatedDecisionPacketValidationResult(
            valid=False,
            errors=("packet must be an object",),
        )

    _validate_top_level_packet(packet, errors)
    _validate_market_snapshot(packet.get("market_snapshot"), errors)
    artifact_ids = _validate_input_artifacts(packet.get("input_artifacts"), errors)
    observation_count = _validate_record_sections(packet.get("record_sections"), artifact_ids, errors)
    _validate_operator_review(packet.get("operator_review"), errors)
    _validate_summary_counts(packet, observation_count, errors)
    _validate_safety_boundaries(packet.get("safety_boundaries"), errors)
    _validate_string_array(packet.get("operator_notes"), "$.operator_notes", errors)
    _validate_string_array(packet.get("warnings"), "$.warnings", errors)
    _validate_string_array(packet.get("errors"), "$.errors", errors)

    for path in _find_forbidden_decision_terms(packet):
        errors.append(f"forbidden guidance/scoring/action field detected in packet at {path}")

    return SimulatedDecisionPacketValidationResult(valid=not errors, errors=tuple(errors))


def _validate_top_level_packet(packet: dict[str, Any], errors: list[str]) -> None:
    _require_exact_fields(packet, required_packet_fields(), "$", errors)
    _require_value(
        packet,
        "contract_version",
        SIMULATED_DECISION_PACKET_CONTRACT_VERSION,
        "$.contract_version",
        errors,
    )
    _require_value(packet, "run_mode", LOCAL_RUN_MODE, "$.run_mode", errors)
    _require_value(packet, "local_only", True, "$.local_only", errors)
    _require_value(packet, "operator_review_required", True, "$.operator_review_required", errors)
    _require_value(packet, "packet_state", PACKET_STATE, "$.packet_state", errors)

    packet_id = packet.get("packet_id")
    if not isinstance(packet_id, str) or not _PACKET_ID_RE.fullmatch(packet_id):
        errors.append("$.packet_id must be a lowercase local identifier")

    created_at = packet.get("created_at")
    if not isinstance(created_at, str) or not _UTC_TIMESTAMP_RE.fullmatch(created_at):
        errors.append("$.created_at must be a UTC timestamp formatted as YYYY-MM-DDTHH:MM:SSZ")

    schema_reference = packet.get("schema_reference")
    _validate_local_reference(schema_reference, "$.schema_reference", errors)
    if schema_reference != "pm_bot/simulated_decisions/schemas/simulated_decision_packet.schema.v1.json":
        errors.append("$.schema_reference must point to the simulated decision packet schema v1 artifact")


def _validate_market_snapshot(value: Any, errors: list[str]) -> None:
    required = tuple(SIMULATED_DECISION_PACKET_SCHEMA["properties"]["market_snapshot"]["required_fields"])
    if not _require_object(value, "$.market_snapshot", errors):
        return

    _require_exact_fields(value, required, "$.market_snapshot", errors)
    for field in ("market_id", "market_title", "question_text", "status"):
        _require_non_empty_string(value.get(field), f"$.market_snapshot.{field}", errors)
    _validate_local_reference(value.get("local_reference"), "$.market_snapshot.local_reference", errors)


def _validate_input_artifacts(value: Any, errors: list[str]) -> frozenset[str]:
    required = tuple(SIMULATED_DECISION_PACKET_SCHEMA["properties"]["input_artifacts"]["items"]["required_fields"])
    artifact_ids: set[str] = set()
    if not isinstance(value, list):
        errors.append("$.input_artifacts must be an array")
        return frozenset()

    for index, artifact in enumerate(value):
        path = f"$.input_artifacts[{index}]"
        if not _require_object(artifact, path, errors):
            continue
        _require_exact_fields(artifact, required, path, errors)
        _require_non_empty_string(artifact.get("artifact_id"), f"{path}.artifact_id", errors)
        _require_non_empty_string(artifact.get("artifact_type"), f"{path}.artifact_type", errors)
        _require_non_empty_string(artifact.get("description"), f"{path}.description", errors)
        _require_value(artifact, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _validate_local_reference(artifact.get("local_reference"), f"{path}.local_reference", errors)
        if isinstance(artifact.get("artifact_id"), str):
            artifact_ids.add(artifact["artifact_id"])
    return frozenset(artifact_ids)


def _validate_record_sections(value: Any, artifact_ids: frozenset[str], errors: list[str]) -> int:
    required = tuple(SIMULATED_DECISION_PACKET_SCHEMA["properties"]["record_sections"]["items"]["required_fields"])
    observation_count = 0
    if not isinstance(value, list):
        errors.append("$.record_sections must be an array")
        return 0

    for section_index, section in enumerate(value):
        section_path = f"$.record_sections[{section_index}]"
        if not _require_object(section, section_path, errors):
            continue
        _require_exact_fields(section, required, section_path, errors)
        _require_non_empty_string(section.get("section_id"), f"{section_path}.section_id", errors)
        _require_non_empty_string(section.get("section_label"), f"{section_path}.section_label", errors)
        _require_value(
            section,
            "operator_review_status",
            OPERATOR_REVIEW_STATUS,
            f"{section_path}.operator_review_status",
            errors,
        )

        observations = section.get("observations")
        if not isinstance(observations, list):
            errors.append(f"{section_path}.observations must be an array")
            continue
        observation_count += len(observations)
        for observation_index, observation in enumerate(observations):
            observation_path = f"{section_path}.observations[{observation_index}]"
            _validate_observation(observation, observation_path, artifact_ids, errors)
    return observation_count


def _validate_observation(
    observation: Any,
    path: str,
    artifact_ids: frozenset[str],
    errors: list[str],
) -> None:
    if not _require_object(observation, path, errors):
        return
    _require_non_empty_string(observation.get("observation_id"), f"{path}.observation_id", errors)
    _require_non_empty_string(observation.get("label"), f"{path}.label", errors)
    _require_value(observation, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)

    source_artifact_ids = observation.get("source_artifact_ids")
    if not isinstance(source_artifact_ids, list) or not source_artifact_ids:
        errors.append(f"{path}.source_artifact_ids must be a non-empty array")
        return
    for artifact_index, artifact_id in enumerate(source_artifact_ids):
        artifact_path = f"{path}.source_artifact_ids[{artifact_index}]"
        if not isinstance(artifact_id, str) or not artifact_id:
            errors.append(f"{artifact_path} must be a non-empty string")
        elif artifact_id not in artifact_ids:
            errors.append(f"{artifact_path} must reference a declared input artifact")


def _validate_operator_review(value: Any, errors: list[str]) -> None:
    required = tuple(SIMULATED_DECISION_PACKET_SCHEMA["properties"]["operator_review"]["required_fields"])
    if not _require_object(value, "$.operator_review", errors):
        return

    _require_exact_fields(value, required, "$.operator_review", errors)
    _require_value(value, "status", OPERATOR_REVIEW_STATUS, "$.operator_review.status", errors)
    if value.get("reviewed_by") is not None:
        errors.append("$.operator_review.reviewed_by must be null before operator review")
    if value.get("reviewed_at") is not None:
        errors.append("$.operator_review.reviewed_at must be null before operator review")
    _validate_string_array(value.get("notes"), "$.operator_review.notes", errors)


def _validate_summary_counts(packet: dict[str, Any], observation_count: int, errors: list[str]) -> None:
    required = tuple(SIMULATED_DECISION_PACKET_SCHEMA["properties"]["summary_counts"]["required_fields"])
    value = packet.get("summary_counts")
    if not _require_object(value, "$.summary_counts", errors):
        return

    _require_exact_fields(value, required, "$.summary_counts", errors)
    expected = {
        "input_artifacts": len(packet.get("input_artifacts")) if isinstance(packet.get("input_artifacts"), list) else 0,
        "record_sections": len(packet.get("record_sections")) if isinstance(packet.get("record_sections"), list) else 0,
        "observations": observation_count,
        "warnings": len(packet.get("warnings")) if isinstance(packet.get("warnings"), list) else 0,
    }
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            errors.append(f"$.summary_counts.{field} must match packet content: {expected_value}")


def _validate_safety_boundaries(value: Any, errors: list[str]) -> None:
    required = tuple(SIMULATED_DECISION_PACKET_SCHEMA["properties"]["safety_boundaries"]["required_fields"])
    if not _require_object(value, "$.safety_boundaries", errors):
        return

    _require_exact_fields(value, required, "$.safety_boundaries", errors)
    if value != SIMULATED_DECISION_PACKET_SCHEMA["safety_boundaries"]:
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


def _require_value(
    value: dict[str, Any],
    field: str,
    expected: Any,
    path: str,
    errors: list[str],
) -> None:
    if value.get(field) != expected:
        errors.append(f"{path} must be {expected!r}")


def _require_non_empty_string(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{path} must be a non-empty string")


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
        errors.append(f"{path} must point to a local fixture or simulated decision artifact")
        return

    resolved = (_WORKSPACE_ROOT / value).resolve()
    try:
        resolved.relative_to(_WORKSPACE_ROOT)
    except ValueError:
        errors.append(f"{path} must stay inside the local workspace")
        return
    if not resolved.exists():
        errors.append(f"{path} must point to an existing local artifact")


def _find_forbidden_decision_terms(value: Any, path: str = "$") -> tuple[str, ...]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_forbidden_token(str(key)):
                hits.append(key_path)
            hits.extend(_find_forbidden_decision_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_forbidden_decision_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_forbidden_token(value):
        hits.append(path)
    return tuple(hits)


def _has_forbidden_token(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & _FORBIDDEN_DECISION_TOKENS)
