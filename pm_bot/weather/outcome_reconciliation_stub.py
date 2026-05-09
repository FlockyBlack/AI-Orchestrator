from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

RECONCILIATION_REQUEST_CONTRACT_VERSION = "pmbot_weather_outcome_reconciliation_request.v1"
RECONCILIATION_RECORD_CONTRACT_VERSION = "pmbot_weather_outcome_reconciliation_record.v1"

LOCAL_RUN_MODE = "local_fixture_only"
RECONCILIATION_RECORD_STATE = "assembled_for_operator_review"
AUTOMATED_OUTCOME_STATUS = "not_performed"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

NETWORK_PREFIXES = ("http://", "https://", "ws://", "wss://")
ALLOWED_LOCAL_REFERENCE_PREFIXES = ("pm_bot/tests/fixtures/", "docs/")

FORBIDDEN_DECISION_FIELD_TOKENS = frozenset(
    {
        "probability",
        "ev",
        "edge",
        "confidence",
        "side",
        "recommendation",
        "buy",
        "sell",
        "hold",
        "enter",
        "exit",
        "score",
        "scoring",
        "forecast",
        "selection",
        "pick",
    }
)

ALLOWED_TOP_LEVEL_FIELDS = frozenset(
    {
        "contract_version",
        "reconciliation_id",
        "scope",
        "local_only",
        "operator_review_required",
        "market_context",
        "observation_records",
        "outcome_reviews",
        "operator_review_steps",
    }
)

REQUIRED_TOP_LEVEL_FIELDS = ALLOWED_TOP_LEVEL_FIELDS - {"market_context"}

REQUIRED_OBSERVATION_RECORD_FIELDS = frozenset(
    {
        "record_id",
        "source_id",
        "source_label",
        "source_type",
        "local_reference",
        "snapshot_id",
        "measurement_name",
        "observation_date",
        "station_id",
        "reported_value",
        "unit",
        "source_timestamp",
        "operator_review_status",
    }
)

REQUIRED_OUTCOME_REVIEW_FIELDS = frozenset(
    {
        "outcome_id",
        "title",
        "measurement_name",
        "record_ids",
        "operator_review_questions",
        "placeholder_notes",
    }
)


@dataclass(frozen=True)
class ReconciliationValidationResult:
    valid: bool
    errors: tuple[str, ...]


class ReconciliationValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        super().__init__("weather outcome reconciliation request is invalid")
        self.errors = tuple(errors)


def load_reconciliation_request(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ReconciliationValidationError(("reconciliation request JSON must be an object",))
    return data


def validate_reconciliation_request(request: Mapping[str, Any]) -> ReconciliationValidationResult:
    errors: list[str] = []

    unknown_fields = sorted(set(request) - ALLOWED_TOP_LEVEL_FIELDS)
    if unknown_fields:
        errors.append(f"unknown top-level fields: {', '.join(unknown_fields)}")

    missing_fields = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(request))
    if missing_fields:
        errors.append(f"missing required fields: {', '.join(missing_fields)}")

    if request.get("contract_version") != RECONCILIATION_REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {RECONCILIATION_REQUEST_CONTRACT_VERSION}")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")

    errors.extend(_find_forbidden_decision_fields(request))

    observation_records = request.get("observation_records")
    if not isinstance(observation_records, list) or not observation_records:
        errors.append("observation_records must be a non-empty list")
        observation_records = []
    records_by_id = _validate_observation_records(observation_records, errors)

    outcome_reviews = request.get("outcome_reviews")
    if not isinstance(outcome_reviews, list) or not outcome_reviews:
        errors.append("outcome_reviews must be a non-empty list")
        outcome_reviews = []
    _validate_outcome_reviews(outcome_reviews, records_by_id, errors)

    operator_review_steps = request.get("operator_review_steps")
    if not _is_non_empty_string_list(operator_review_steps):
        errors.append("operator_review_steps must be a non-empty list of strings")

    return ReconciliationValidationResult(valid=not errors, errors=tuple(errors))


def build_reconciliation_record(request: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_reconciliation_request(request)
    if not validation.valid:
        raise ReconciliationValidationError(validation.errors)

    reconciliation_id = _string_field(request, "reconciliation_id")
    records_by_id = {record["record_id"]: record for record in request["observation_records"]}
    review_records = [
        _outcome_review_record(reconciliation_id, outcome_review, records_by_id)
        for outcome_review in request["outcome_reviews"]
    ]
    return {
        "contract_version": RECONCILIATION_RECORD_CONTRACT_VERSION,
        "reconciliation_id": reconciliation_id,
        "run_id": _stable_run_id(request),
        "run_mode": LOCAL_RUN_MODE,
        "scope": _string_field(request, "scope"),
        "local_only": True,
        "operator_review_required": True,
        "market_context": dict(request.get("market_context") or {}),
        "summary_counts": {
            "observation_records": len(request["observation_records"]),
            "outcome_reviews": len(review_records),
            "warnings": 0,
        },
        "record_inventory": [
            _observation_record_inventory_entry(record) for record in request["observation_records"]
        ],
        "outcome_review_records": review_records,
        "operator_review": {
            "status": OPERATOR_REVIEW_STATUS,
            "required_steps": list(request["operator_review_steps"]),
        },
        "safety_boundaries": {
            "offline_inputs_only": True,
            "network_calls_allowed": False,
            "llm_calls_allowed": False,
            "external_market_api_allowed": False,
            "wallet_or_order_code_allowed": False,
            "runtime_wiring_allowed": False,
            "scheduler_or_worker_allowed": False,
            "trade_action_guidance_allowed": False,
            "automated_outcome_resolution_allowed": False,
            "operator_review_gate_required": True,
        },
        "warnings": [],
        "errors": [],
    }


def build_operator_report(reconciliation_record: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Weather Outcome Reconciliation Placeholder",
        "",
        f"- Contract: `{reconciliation_record['contract_version']}`",
        f"- Reconciliation: `{reconciliation_record['reconciliation_id']}`",
        f"- Run: `{reconciliation_record['run_id']}`",
        f"- Run mode: `{reconciliation_record['run_mode']}`",
        f"- Operator review: `{reconciliation_record['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Observation records: {reconciliation_record['summary_counts']['observation_records']}",
        f"- Outcome review records: {reconciliation_record['summary_counts']['outcome_reviews']}",
        f"- Warnings: {reconciliation_record['summary_counts']['warnings']}",
        "",
        "## Outcome Review Records",
        "",
    ]

    for review_record in reconciliation_record["outcome_review_records"]:
        lines.append(
            "- "
            f"`{review_record['review_record_id']}`: {review_record['title']}; "
            f"{len(review_record['referenced_records'])} referenced record(s); "
            f"automated outcome `{review_record['automated_outcome_status']}`; "
            f"review `{review_record['operator_review_status']}`."
        )

    lines.extend(
        [
            "",
            "## Operator Review",
            "",
        ]
    )
    for step in reconciliation_record["operator_review"]["required_steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Uses local fixture/static inputs only.",
            "- Makes no network, LLM, market API, wallet, order, or runtime calls.",
            "- Produces placeholder review records for human operators only.",
            "- Leaves final weather outcome status outside this artifact.",
            "- Includes no market instruction.",
            "",
        ]
    )
    return "\n".join(lines)


def write_reconciliation_outputs(
    request_path: str | Path,
    output_record_path: str | Path,
    output_report_path: str | Path,
) -> dict[str, Any]:
    request = load_reconciliation_request(request_path)
    reconciliation_record = build_reconciliation_record(request)

    record_destination = Path(output_record_path)
    record_destination.parent.mkdir(parents=True, exist_ok=True)
    record_destination.write_text(_json_dumps(reconciliation_record), encoding="utf-8")

    report_destination = Path(output_report_path)
    report_destination.parent.mkdir(parents=True, exist_ok=True)
    report_destination.write_text(build_operator_report(reconciliation_record), encoding="utf-8")

    return reconciliation_record


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT weather outcome reconciliation placeholder.")
    parser.add_argument("--request", required=True, help="Path to a local reconciliation request JSON file.")
    parser.add_argument(
        "--output-record",
        required=True,
        help="Path where the reconciliation record JSON will be written.",
    )
    parser.add_argument(
        "--output-report",
        required=True,
        help="Path where the operator Markdown report will be written.",
    )
    args = parser.parse_args(argv)

    try:
        write_reconciliation_outputs(args.request, args.output_record, args.output_report)
    except ReconciliationValidationError as exc:
        for error in exc.errors:
            print(f"error: {error}")
        return 1
    return 0


def _validate_observation_records(
    observation_records: Sequence[Any],
    errors: list[str],
) -> dict[str, Mapping[str, Any]]:
    records_by_id: dict[str, Mapping[str, Any]] = {}
    for index, record in enumerate(observation_records):
        path = f"observation_records[{index}]"
        if not isinstance(record, Mapping):
            errors.append(f"{path} must be an object")
            continue

        missing = sorted(REQUIRED_OBSERVATION_RECORD_FIELDS - set(record))
        if missing:
            errors.append(f"{path} missing required fields: {', '.join(missing)}")

        for field in REQUIRED_OBSERVATION_RECORD_FIELDS - {"reported_value"}:
            value = record.get(field)
            if not isinstance(value, str) or not value:
                errors.append(f"{path}.{field} must be a non-empty string")

        reported_value = record.get("reported_value")
        if not _is_json_scalar(reported_value):
            errors.append(f"{path}.reported_value must be a JSON scalar value")

        record_id = record.get("record_id")
        if isinstance(record_id, str) and record_id:
            if record_id in records_by_id:
                errors.append(f"{path}.record_id must be unique")
            else:
                records_by_id[record_id] = record

        local_reference = record.get("local_reference")
        if isinstance(local_reference, str) and local_reference:
            if local_reference.lower().startswith(NETWORK_PREFIXES):
                errors.append(f"{path}.local_reference must point to a local fixture or static artifact")
            elif not _is_allowed_local_reference(local_reference):
                errors.append(f"{path}.local_reference must stay under an allowed local fixture/static path")

        if record.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")

    return records_by_id


def _validate_outcome_reviews(
    outcome_reviews: Sequence[Any],
    records_by_id: Mapping[str, Mapping[str, Any]],
    errors: list[str],
) -> None:
    outcome_ids: set[str] = set()
    for index, outcome_review in enumerate(outcome_reviews):
        path = f"outcome_reviews[{index}]"
        if not isinstance(outcome_review, Mapping):
            errors.append(f"{path} must be an object")
            continue

        missing = sorted(REQUIRED_OUTCOME_REVIEW_FIELDS - set(outcome_review))
        if missing:
            errors.append(f"{path} missing required fields: {', '.join(missing)}")

        for field in REQUIRED_OUTCOME_REVIEW_FIELDS - {
            "record_ids",
            "operator_review_questions",
            "placeholder_notes",
        }:
            value = outcome_review.get(field)
            if not isinstance(value, str) or not value:
                errors.append(f"{path}.{field} must be a non-empty string")

        outcome_id = outcome_review.get("outcome_id")
        if isinstance(outcome_id, str) and outcome_id:
            if outcome_id in outcome_ids:
                errors.append(f"{path}.outcome_id must be unique")
            else:
                outcome_ids.add(outcome_id)

        record_ids = outcome_review.get("record_ids")
        if not _is_non_empty_string_list(record_ids):
            errors.append(f"{path}.record_ids must be a non-empty list of strings")
        else:
            missing_record_ids = sorted(set(record_ids) - set(records_by_id))
            if missing_record_ids:
                errors.append(f"{path}.record_ids references unknown records: {', '.join(missing_record_ids)}")
            expected_measurement_name = outcome_review.get("measurement_name")
            if isinstance(expected_measurement_name, str) and expected_measurement_name:
                mismatched_record_ids = sorted(
                    record_id
                    for record_id in record_ids
                    if record_id in records_by_id
                    and records_by_id[record_id].get("measurement_name") != expected_measurement_name
                )
                if mismatched_record_ids:
                    errors.append(
                        f"{path}.record_ids references records for a different measurement: "
                        f"{', '.join(mismatched_record_ids)}"
                    )

        if not _is_non_empty_string_list(outcome_review.get("operator_review_questions")):
            errors.append(f"{path}.operator_review_questions must be a non-empty list of strings")
        if not _is_non_empty_string_list(outcome_review.get("placeholder_notes")):
            errors.append(f"{path}.placeholder_notes must be a non-empty list of strings")


def _observation_record_inventory_entry(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "record_id": record["record_id"],
        "source_id": record["source_id"],
        "source_label": record["source_label"],
        "source_type": record["source_type"],
        "local_reference": record["local_reference"],
        "snapshot_id": record["snapshot_id"],
        "measurement_name": record["measurement_name"],
        "observation_date": record["observation_date"],
        "station_id": record["station_id"],
        "reported_value": record["reported_value"],
        "unit": record["unit"],
        "source_timestamp": record["source_timestamp"],
        "runner_state": RECONCILIATION_RECORD_STATE,
        "operator_review_status": record["operator_review_status"],
    }


def _outcome_review_record(
    reconciliation_id: str,
    outcome_review: Mapping[str, Any],
    records_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    referenced_records = [
        _referenced_observation_record(records_by_id[record_id]) for record_id in outcome_review["record_ids"]
    ]
    return {
        "review_record_id": f"{reconciliation_id}.{outcome_review['outcome_id']}.operator_review",
        "outcome_id": outcome_review["outcome_id"],
        "title": outcome_review["title"],
        "measurement_name": outcome_review["measurement_name"],
        "record_ids": list(outcome_review["record_ids"]),
        "referenced_records": referenced_records,
        "operator_review_questions": list(outcome_review["operator_review_questions"]),
        "placeholder_notes": list(outcome_review["placeholder_notes"]),
        "runner_state": RECONCILIATION_RECORD_STATE,
        "automated_outcome_status": AUTOMATED_OUTCOME_STATUS,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
    }


def _referenced_observation_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "record_id": record["record_id"],
        "source_id": record["source_id"],
        "measurement_name": record["measurement_name"],
        "observation_date": record["observation_date"],
        "station_id": record["station_id"],
        "reported_value": record["reported_value"],
        "unit": record["unit"],
        "source_timestamp": record["source_timestamp"],
        "operator_review_status": record["operator_review_status"],
    }


def _stable_run_id(request: Mapping[str, Any]) -> str:
    reconciliation_id = _string_field(request, "reconciliation_id")
    digest = hashlib.sha256(_json_dumps(request).encode("utf-8")).hexdigest()[:12]
    return f"{reconciliation_id}-{digest}"


def _find_forbidden_decision_fields(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, Mapping):
        for raw_key, nested_value in value.items():
            key = str(raw_key)
            key_path = f"{path}.{key}"
            if _contains_forbidden_token(key):
                hits.append(f"forbidden scoring/action field detected at {key_path}")
            hits.extend(_find_forbidden_decision_fields(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_forbidden_decision_fields(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _contains_forbidden_token(value):
        hits.append(f"forbidden scoring/action text detected at {path}")
    return hits


def _contains_forbidden_token(value: str) -> bool:
    normalized = []
    for character in value.lower():
        normalized.append(character if character.isalnum() else "_")
    tokens = {token for token in "".join(normalized).split("_") if token}
    return bool(tokens & FORBIDDEN_DECISION_FIELD_TOKENS)


def _is_allowed_local_reference(local_reference: str) -> bool:
    candidate = Path(local_reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    normalized = local_reference.replace("\\", "/")
    return any(normalized.startswith(prefix) for prefix in ALLOWED_LOCAL_REFERENCE_PREFIXES)


def _is_json_scalar(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, str):
        return bool(value)
    return isinstance(value, (int, float))


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _string_field(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ReconciliationValidationError((f"{key} must be a non-empty string",))
    return value


def _json_dumps(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
