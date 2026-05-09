from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.weather.observation_ledger_refresher import OBSERVATION_LEDGER_CONTRACT_VERSION
from pm_bot.weather.outcome_reconciliation_stub import (
    AUTOMATED_OUTCOME_STATUS,
    RECONCILIATION_RECORD_CONTRACT_VERSION,
)

OPERATOR_REVIEW_SURFACE_CONTRACT_VERSION = "pmbot_weather_operator_review_surface.v1"

LOCAL_RUN_MODE = "local_fixture_only"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
SURFACE_STATE = "assembled_for_operator_review"

NETWORK_PREFIXES = ("http://", "https://", "ws://", "wss://")
FORBIDDEN_ARTIFACT_PATH_PARTS = frozenset(
    {
        ".git",
        ".codex",
        "runtime",
        "dispatcher",
        "run_codex",
        "llm",
        "wallet",
        "trading",
        "orders",
    }
)

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

LEDGER_RECORD_REQUIRED_FIELDS = frozenset(
    {
        "record_id",
        "source_id",
        "source_label",
        "source_type",
        "local_reference",
        "snapshot_id",
        "observation_date",
        "station_id",
        "measurement_name",
        "reported_value",
        "unit",
        "source_timestamp",
        "operator_review_status",
    }
)

RECONCILIATION_RECORD_REQUIRED_FIELDS = frozenset(
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

OUTCOME_REVIEW_REQUIRED_FIELDS = frozenset(
    {
        "review_record_id",
        "outcome_id",
        "title",
        "measurement_name",
        "record_ids",
        "referenced_records",
        "operator_review_questions",
        "placeholder_notes",
        "runner_state",
        "automated_outcome_status",
        "operator_review_status",
    }
)

RECORD_COMPARISON_FIELDS = (
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
)

REFERENCED_RECORD_COMPARISON_FIELDS = (
    "source_id",
    "measurement_name",
    "observation_date",
    "station_id",
    "reported_value",
    "unit",
    "source_timestamp",
    "operator_review_status",
)


@dataclass(frozen=True)
class OperatorReviewSurfaceValidationResult:
    valid: bool
    errors: tuple[str, ...]


class OperatorReviewSurfaceValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        super().__init__("weather operator review surface inputs are invalid")
        self.errors = tuple(errors)


def load_review_artifact(path: str | Path) -> dict[str, Any]:
    path_text = str(path)
    if path_text.lower().startswith(NETWORK_PREFIXES):
        raise OperatorReviewSurfaceValidationError(("artifact path must be local",))
    if _is_forbidden_artifact_path(path):
        raise OperatorReviewSurfaceValidationError(("artifact path is outside the weather review surface boundary",))

    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise OperatorReviewSurfaceValidationError(("artifact JSON must be an object",))
    return data


def validate_review_surface_inputs(
    ledger: Mapping[str, Any],
    reconciliation_record: Mapping[str, Any],
) -> OperatorReviewSurfaceValidationResult:
    errors: list[str] = []
    errors.extend(_find_forbidden_decision_fields(ledger, "$.ledger"))
    errors.extend(_find_forbidden_decision_fields(reconciliation_record, "$.reconciliation_record"))

    ledger_records_by_id = _validate_ledger(ledger, errors)
    reconciliation_records_by_id = _validate_reconciliation_record(reconciliation_record, errors)
    _validate_cross_artifact_links(ledger_records_by_id, reconciliation_record, reconciliation_records_by_id, errors)

    ledger_context = ledger.get("market_context") or {}
    reconciliation_context = reconciliation_record.get("market_context") or {}
    if ledger_context and reconciliation_context and ledger_context != reconciliation_context:
        errors.append("market_context must match when both artifacts provide it")

    return OperatorReviewSurfaceValidationResult(valid=not errors, errors=tuple(errors))


def build_operator_review_surface(
    ledger: Mapping[str, Any],
    reconciliation_record: Mapping[str, Any],
) -> dict[str, Any]:
    validation = validate_review_surface_inputs(ledger, reconciliation_record)
    if not validation.valid:
        raise OperatorReviewSurfaceValidationError(validation.errors)

    ledger_records_by_id = {record["record_id"]: record for record in ledger["records"]}
    reconciliation_records_by_id = {
        record["record_id"]: record for record in reconciliation_record["record_inventory"]
    }
    referenced_by_review_id = _referenced_review_index(reconciliation_record["outcome_review_records"])
    record_links = [
        _record_link_panel(record, reconciliation_records_by_id.get(record["record_id"]), referenced_by_review_id)
        for record in ledger["records"]
    ]

    warnings = _surface_warnings(record_links)
    surface = {
        "contract_version": OPERATOR_REVIEW_SURFACE_CONTRACT_VERSION,
        "surface_id": _stable_surface_id(ledger, reconciliation_record),
        "run_mode": LOCAL_RUN_MODE,
        "scope": "weather_operator_review_surface",
        "local_only": True,
        "operator_review_required": True,
        "source_artifacts": {
            "ledger_id": ledger["ledger_id"],
            "ledger_refresh_id": ledger["refresh_id"],
            "reconciliation_id": reconciliation_record["reconciliation_id"],
            "reconciliation_run_id": reconciliation_record["run_id"],
        },
        "market_context": dict(ledger.get("market_context") or reconciliation_record.get("market_context") or {}),
        "summary_counts": {
            "ledger_records": len(ledger["records"]),
            "reconciliation_inventory_records": len(reconciliation_record["record_inventory"]),
            "outcome_review_records": len(reconciliation_record["outcome_review_records"]),
            "record_links": len(record_links),
            "unlinked_ledger_records": sum(
                1 for link in record_links if not link["reconciliation_inventory_present"]
            ),
            "warnings": len(warnings),
        },
        "ledger_record_panels": [
            _ledger_record_panel(record, referenced_by_review_id) for record in ledger["records"]
        ],
        "record_link_panels": record_links,
        "reconciliation_review_panels": [
            _reconciliation_review_panel(review_record, ledger_records_by_id)
            for review_record in reconciliation_record["outcome_review_records"]
        ],
        "operator_review": {
            "status": OPERATOR_REVIEW_STATUS,
            "required_steps": [
                "Inspect each ledger record panel against the named local source artifact.",
                "Inspect each record link panel before using reconciliation review records.",
                "Keep any final weather outcome record outside this review surface.",
            ],
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
            "weather_outcome_evaluation_allowed": False,
            "automated_outcome_resolution_allowed": False,
            "operator_review_gate_required": True,
        },
        "warnings": warnings,
        "errors": [],
    }
    return surface


def build_operator_report(surface: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Weather Operator Review Surface",
        "",
        f"- Contract: `{surface['contract_version']}`",
        f"- Surface: `{surface['surface_id']}`",
        f"- Ledger: `{surface['source_artifacts']['ledger_id']}`",
        f"- Ledger refresh: `{surface['source_artifacts']['ledger_refresh_id']}`",
        f"- Reconciliation: `{surface['source_artifacts']['reconciliation_id']}`",
        f"- Reconciliation run: `{surface['source_artifacts']['reconciliation_run_id']}`",
        f"- Operator review: `{surface['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Ledger records: {surface['summary_counts']['ledger_records']}",
        f"- Reconciliation inventory records: {surface['summary_counts']['reconciliation_inventory_records']}",
        f"- Outcome review records: {surface['summary_counts']['outcome_review_records']}",
        f"- Record links: {surface['summary_counts']['record_links']}",
        f"- Unlinked ledger records: {surface['summary_counts']['unlinked_ledger_records']}",
        f"- Warnings: {surface['summary_counts']['warnings']}",
        "",
        "## Ledger Records",
        "",
    ]

    for panel in surface["ledger_record_panels"]:
        review_ids = ", ".join(f"`{review_id}`" for review_id in panel["referenced_by_review_ids"]) or "`none`"
        lines.append(
            "- "
            f"`{panel['record_id']}`: {panel['measurement_name']} = "
            f"{panel['reported_value']} {panel['unit']} for "
            f"{panel['station_id']} on {panel['observation_date']}; "
            f"source `{panel['source_id']}`; local `{panel['local_reference']}`; "
            f"review `{panel['operator_review_status']}`; reconciliation reviews {review_ids}."
        )

    lines.extend(["", "## Record Links", ""])
    for panel in surface["record_link_panels"]:
        review_ids = ", ".join(f"`{review_id}`" for review_id in panel["referenced_by_review_ids"]) or "`none`"
        lines.append(
            "- "
            f"`{panel['record_id']}`: ledger present `{panel['ledger_record_present']}`; "
            f"reconciliation inventory present `{panel['reconciliation_inventory_present']}`; "
            f"status `{panel['operator_review_status']}`; reviews {review_ids}."
        )

    lines.extend(["", "## Reconciliation Review Records", ""])
    for panel in surface["reconciliation_review_panels"]:
        record_ids = ", ".join(f"`{record_id}`" for record_id in panel["record_ids"])
        lines.append(
            "- "
            f"`{panel['review_record_id']}`: {panel['title']}; "
            f"records {record_ids}; automated outcome `{panel['automated_outcome_status']}`; "
            f"review `{panel['operator_review_status']}`."
        )

    lines.extend(["", "## Operator Review", ""])
    for step in surface["operator_review"]["required_steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Uses local fixture/static inputs only.",
            "- Makes no network, LLM, market API, wallet, order, or runtime calls.",
            "- Provides inspection panels for human operators only.",
            "- Does not evaluate weather outcomes or provide trade action guidance.",
            "",
        ]
    )
    return "\n".join(lines)


def write_review_surface_outputs(
    ledger_path: str | Path,
    reconciliation_record_path: str | Path,
    output_surface_path: str | Path,
    output_report_path: str | Path,
) -> dict[str, Any]:
    ledger = load_review_artifact(ledger_path)
    reconciliation_record = load_review_artifact(reconciliation_record_path)
    surface = build_operator_review_surface(ledger, reconciliation_record)

    surface_destination = Path(output_surface_path)
    surface_destination.parent.mkdir(parents=True, exist_ok=True)
    surface_destination.write_text(_json_dumps(surface), encoding="utf-8")

    report_destination = Path(output_report_path)
    report_destination.parent.mkdir(parents=True, exist_ok=True)
    report_destination.write_text(build_operator_report(surface), encoding="utf-8")

    return surface


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT weather operator review surface.")
    parser.add_argument("--ledger", required=True, help="Path to a local weather observation ledger JSON file.")
    parser.add_argument(
        "--reconciliation-record",
        required=True,
        help="Path to a local weather reconciliation record JSON file.",
    )
    parser.add_argument(
        "--output-surface",
        required=True,
        help="Path where the operator review surface JSON will be written.",
    )
    parser.add_argument(
        "--output-report",
        required=True,
        help="Path where the operator Markdown report will be written.",
    )
    args = parser.parse_args(argv)

    try:
        write_review_surface_outputs(
            args.ledger,
            args.reconciliation_record,
            args.output_surface,
            args.output_report,
        )
    except OperatorReviewSurfaceValidationError as exc:
        for error in exc.errors:
            print(f"error: {error}")
        return 1
    return 0


def _validate_ledger(ledger: Mapping[str, Any], errors: list[str]) -> dict[str, Mapping[str, Any]]:
    if ledger.get("contract_version") != OBSERVATION_LEDGER_CONTRACT_VERSION:
        errors.append(f"ledger.contract_version must be {OBSERVATION_LEDGER_CONTRACT_VERSION}")
    if ledger.get("local_only") is not True:
        errors.append("ledger.local_only must be true")
    if ledger.get("operator_review_required") is not True:
        errors.append("ledger.operator_review_required must be true")

    for field in ("ledger_id", "refresh_id", "run_mode", "scope"):
        if not isinstance(ledger.get(field), str) or not ledger.get(field):
            errors.append(f"ledger.{field} must be a non-empty string")

    _validate_operator_review_block(ledger.get("operator_review"), "ledger.operator_review", errors)
    _validate_safety_boundaries(ledger.get("safety_boundaries"), "ledger.safety_boundaries", errors)

    records = ledger.get("records")
    if not isinstance(records, list) or not records:
        errors.append("ledger.records must be a non-empty list")
        return {}

    records_by_id: dict[str, Mapping[str, Any]] = {}
    for index, record in enumerate(records):
        path = f"ledger.records[{index}]"
        if not isinstance(record, Mapping):
            errors.append(f"{path} must be an object")
            continue
        _validate_record_fields(record, LEDGER_RECORD_REQUIRED_FIELDS, path, errors)

        record_id = record.get("record_id")
        if isinstance(record_id, str) and record_id:
            if record_id in records_by_id:
                errors.append(f"{path}.record_id must be unique")
            else:
                records_by_id[record_id] = record

        if record.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")

    return records_by_id


def _validate_reconciliation_record(
    reconciliation_record: Mapping[str, Any],
    errors: list[str],
) -> dict[str, Mapping[str, Any]]:
    if reconciliation_record.get("contract_version") != RECONCILIATION_RECORD_CONTRACT_VERSION:
        errors.append(f"reconciliation_record.contract_version must be {RECONCILIATION_RECORD_CONTRACT_VERSION}")
    if reconciliation_record.get("local_only") is not True:
        errors.append("reconciliation_record.local_only must be true")
    if reconciliation_record.get("operator_review_required") is not True:
        errors.append("reconciliation_record.operator_review_required must be true")

    for field in ("reconciliation_id", "run_id", "run_mode", "scope"):
        if not isinstance(reconciliation_record.get(field), str) or not reconciliation_record.get(field):
            errors.append(f"reconciliation_record.{field} must be a non-empty string")

    _validate_operator_review_block(
        reconciliation_record.get("operator_review"),
        "reconciliation_record.operator_review",
        errors,
    )
    _validate_safety_boundaries(
        reconciliation_record.get("safety_boundaries"),
        "reconciliation_record.safety_boundaries",
        errors,
    )

    record_inventory = reconciliation_record.get("record_inventory")
    if not isinstance(record_inventory, list) or not record_inventory:
        errors.append("reconciliation_record.record_inventory must be a non-empty list")
        record_inventory = []

    records_by_id: dict[str, Mapping[str, Any]] = {}
    for index, record in enumerate(record_inventory):
        path = f"reconciliation_record.record_inventory[{index}]"
        if not isinstance(record, Mapping):
            errors.append(f"{path} must be an object")
            continue
        _validate_record_fields(record, RECONCILIATION_RECORD_REQUIRED_FIELDS, path, errors)
        record_id = record.get("record_id")
        if isinstance(record_id, str) and record_id:
            if record_id in records_by_id:
                errors.append(f"{path}.record_id must be unique")
            else:
                records_by_id[record_id] = record
        if record.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")

    outcome_review_records = reconciliation_record.get("outcome_review_records")
    if not isinstance(outcome_review_records, list) or not outcome_review_records:
        errors.append("reconciliation_record.outcome_review_records must be a non-empty list")
        return records_by_id

    review_ids: set[str] = set()
    for index, review_record in enumerate(outcome_review_records):
        path = f"reconciliation_record.outcome_review_records[{index}]"
        if not isinstance(review_record, Mapping):
            errors.append(f"{path} must be an object")
            continue
        _validate_outcome_review_record(review_record, records_by_id, review_ids, path, errors)

    return records_by_id


def _validate_cross_artifact_links(
    ledger_records_by_id: Mapping[str, Mapping[str, Any]],
    reconciliation_record: Mapping[str, Any],
    reconciliation_records_by_id: Mapping[str, Mapping[str, Any]],
    errors: list[str],
) -> None:
    missing_from_ledger = sorted(set(reconciliation_records_by_id) - set(ledger_records_by_id))
    if missing_from_ledger:
        errors.append(
            "reconciliation_record.record_inventory references records missing from ledger: "
            + ", ".join(missing_from_ledger)
        )

    for record_id in sorted(set(reconciliation_records_by_id) & set(ledger_records_by_id)):
        ledger_record = ledger_records_by_id[record_id]
        reconciliation_inventory_record = reconciliation_records_by_id[record_id]
        mismatched_fields = [
            field
            for field in RECORD_COMPARISON_FIELDS
            if ledger_record.get(field) != reconciliation_inventory_record.get(field)
        ]
        if mismatched_fields:
            errors.append(f"record {record_id} differs between ledger and reconciliation: {', '.join(mismatched_fields)}")

    for review_record in reconciliation_record.get("outcome_review_records") or []:
        if not isinstance(review_record, Mapping):
            continue
        for referenced_record in review_record.get("referenced_records") or []:
            if not isinstance(referenced_record, Mapping):
                continue
            record_id = referenced_record.get("record_id")
            if not isinstance(record_id, str) or not record_id:
                continue
            ledger_record = ledger_records_by_id.get(record_id)
            if ledger_record is None:
                errors.append(f"review record {review_record.get('review_record_id')} references missing ledger record: {record_id}")
                continue
            mismatched_fields = [
                field
                for field in REFERENCED_RECORD_COMPARISON_FIELDS
                if ledger_record.get(field) != referenced_record.get(field)
            ]
            if mismatched_fields:
                errors.append(
                    f"review record {review_record.get('review_record_id')} referenced record {record_id} "
                    f"differs from ledger: {', '.join(mismatched_fields)}"
                )


def _validate_record_fields(
    record: Mapping[str, Any],
    required_fields: frozenset[str],
    path: str,
    errors: list[str],
) -> None:
    missing = sorted(required_fields - set(record))
    if missing:
        errors.append(f"{path} missing required fields: {', '.join(missing)}")

    for field in required_fields - {"reported_value"}:
        value = record.get(field)
        if not isinstance(value, str) or not value:
            errors.append(f"{path}.{field} must be a non-empty string")

    if not _is_json_scalar(record.get("reported_value")):
        errors.append(f"{path}.reported_value must be a JSON scalar value")


def _validate_outcome_review_record(
    review_record: Mapping[str, Any],
    records_by_id: Mapping[str, Mapping[str, Any]],
    review_ids: set[str],
    path: str,
    errors: list[str],
) -> None:
    missing = sorted(OUTCOME_REVIEW_REQUIRED_FIELDS - set(review_record))
    if missing:
        errors.append(f"{path} missing required fields: {', '.join(missing)}")

    for field in OUTCOME_REVIEW_REQUIRED_FIELDS - {
        "record_ids",
        "referenced_records",
        "operator_review_questions",
        "placeholder_notes",
    }:
        value = review_record.get(field)
        if not isinstance(value, str) or not value:
            errors.append(f"{path}.{field} must be a non-empty string")

    review_record_id = review_record.get("review_record_id")
    if isinstance(review_record_id, str) and review_record_id:
        if review_record_id in review_ids:
            errors.append(f"{path}.review_record_id must be unique")
        else:
            review_ids.add(review_record_id)

    if review_record.get("automated_outcome_status") != AUTOMATED_OUTCOME_STATUS:
        errors.append(f"{path}.automated_outcome_status must be {AUTOMATED_OUTCOME_STATUS}")
    if review_record.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")

    record_ids = review_record.get("record_ids")
    if not _is_non_empty_string_list(record_ids):
        errors.append(f"{path}.record_ids must be a non-empty list of strings")
        record_ids = []
    else:
        missing_records = sorted(set(record_ids) - set(records_by_id))
        if missing_records:
            errors.append(f"{path}.record_ids references unknown records: {', '.join(missing_records)}")

    if not _is_non_empty_string_list(review_record.get("operator_review_questions")):
        errors.append(f"{path}.operator_review_questions must be a non-empty list of strings")
    if not _is_non_empty_string_list(review_record.get("placeholder_notes")):
        errors.append(f"{path}.placeholder_notes must be a non-empty list of strings")

    referenced_records = review_record.get("referenced_records")
    if not isinstance(referenced_records, list) or not referenced_records:
        errors.append(f"{path}.referenced_records must be a non-empty list")
        return

    referenced_record_ids: list[str] = []
    for index, referenced_record in enumerate(referenced_records):
        referenced_path = f"{path}.referenced_records[{index}]"
        if not isinstance(referenced_record, Mapping):
            errors.append(f"{referenced_path} must be an object")
            continue
        _validate_record_fields(
            referenced_record,
            frozenset({"record_id", *REFERENCED_RECORD_COMPARISON_FIELDS}),
            referenced_path,
            errors,
        )
        record_id = referenced_record.get("record_id")
        if isinstance(record_id, str) and record_id:
            referenced_record_ids.append(record_id)

    if record_ids and referenced_record_ids != list(record_ids):
        errors.append(f"{path}.referenced_records must appear in the same order as record_ids")


def _validate_operator_review_block(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return
    if value.get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.status must be {OPERATOR_REVIEW_STATUS}")
    if not _is_non_empty_string_list(value.get("required_steps")):
        errors.append(f"{path}.required_steps must be a non-empty list of strings")


def _validate_safety_boundaries(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return
    if value.get("offline_inputs_only") is not True:
        errors.append(f"{path}.offline_inputs_only must be true")
    for field in (
        "network_calls_allowed",
        "llm_calls_allowed",
        "external_market_api_allowed",
        "wallet_or_order_code_allowed",
        "runtime_wiring_allowed",
        "scheduler_or_worker_allowed",
        "trade_action_guidance_allowed",
    ):
        if value.get(field) is not False:
            errors.append(f"{path}.{field} must be false")


def _ledger_record_panel(
    record: Mapping[str, Any],
    referenced_by_review_id: Mapping[str, Sequence[str]],
) -> dict[str, Any]:
    return {
        "panel_id": f"ledger_record.{record['record_id']}",
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
        "operator_review_status": record["operator_review_status"],
        "referenced_by_review_ids": list(referenced_by_review_id.get(record["record_id"], ())),
        "runner_state": SURFACE_STATE,
        "inspection_points": [
            "Confirm the local source artifact path is expected.",
            "Confirm the station, date, value, unit, and source timestamp are visible.",
            "Confirm the record remains pending operator review.",
        ],
    }


def _record_link_panel(
    ledger_record: Mapping[str, Any],
    reconciliation_record: Mapping[str, Any] | None,
    referenced_by_review_id: Mapping[str, Sequence[str]],
) -> dict[str, Any]:
    return {
        "panel_id": f"record_link.{ledger_record['record_id']}",
        "record_id": ledger_record["record_id"],
        "ledger_record_present": True,
        "reconciliation_inventory_present": reconciliation_record is not None,
        "measurement_name": ledger_record["measurement_name"],
        "observation_date": ledger_record["observation_date"],
        "station_id": ledger_record["station_id"],
        "reported_value": ledger_record["reported_value"],
        "unit": ledger_record["unit"],
        "operator_review_status": ledger_record["operator_review_status"],
        "referenced_by_review_ids": list(referenced_by_review_id.get(ledger_record["record_id"], ())),
        "runner_state": SURFACE_STATE,
    }


def _reconciliation_review_panel(
    review_record: Mapping[str, Any],
    ledger_records_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "panel_id": f"reconciliation_review.{review_record['review_record_id']}",
        "review_record_id": review_record["review_record_id"],
        "outcome_id": review_record["outcome_id"],
        "title": review_record["title"],
        "measurement_name": review_record["measurement_name"],
        "record_ids": list(review_record["record_ids"]),
        "referenced_records": [
            _review_panel_referenced_record(ledger_records_by_id[record_id]) for record_id in review_record["record_ids"]
        ],
        "operator_review_questions": list(review_record["operator_review_questions"]),
        "placeholder_notes": list(review_record["placeholder_notes"]),
        "automated_outcome_status": review_record["automated_outcome_status"],
        "operator_review_status": review_record["operator_review_status"],
        "runner_state": SURFACE_STATE,
    }


def _review_panel_referenced_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "record_id": record["record_id"],
        "source_id": record["source_id"],
        "source_label": record["source_label"],
        "measurement_name": record["measurement_name"],
        "observation_date": record["observation_date"],
        "station_id": record["station_id"],
        "reported_value": record["reported_value"],
        "unit": record["unit"],
        "source_timestamp": record["source_timestamp"],
        "operator_review_status": record["operator_review_status"],
    }


def _referenced_review_index(outcome_review_records: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    referenced_by_review_id: dict[str, list[str]] = {}
    for review_record in outcome_review_records:
        for record_id in review_record["record_ids"]:
            referenced_by_review_id.setdefault(record_id, []).append(review_record["review_record_id"])
    return referenced_by_review_id


def _surface_warnings(record_links: Sequence[Mapping[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for link in record_links:
        if not link["reconciliation_inventory_present"]:
            warnings.append(f"ledger record is not present in reconciliation inventory: {link['record_id']}")
    return warnings


def _stable_surface_id(ledger: Mapping[str, Any], reconciliation_record: Mapping[str, Any]) -> str:
    material = {
        "ledger_id": ledger["ledger_id"],
        "ledger_refresh_id": ledger["refresh_id"],
        "reconciliation_id": reconciliation_record["reconciliation_id"],
        "reconciliation_run_id": reconciliation_record["run_id"],
        "ledger_record_ids": [record["record_id"] for record in ledger["records"]],
        "review_record_ids": [
            review_record["review_record_id"] for review_record in reconciliation_record["outcome_review_records"]
        ],
    }
    digest = hashlib.sha256(_json_dumps(material).encode("utf-8")).hexdigest()[:12]
    return f"{ledger['ledger_id']}.{reconciliation_record['reconciliation_id']}-{digest}"


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


def _is_forbidden_artifact_path(path: str | Path) -> bool:
    candidate = Path(path)
    name = candidate.name.lower()
    if name == ".env" or name.startswith(".env."):
        return True

    parts = {part.lower() for part in candidate.parts}
    if parts & FORBIDDEN_ARTIFACT_PATH_PARTS:
        return True

    normalized = tuple(part.lower() for part in candidate.parts)
    return any(
        normalized[index : index + 2] == ("agent_tasks", "running")
        for index in range(max(len(normalized) - 1, 0))
    )


def _is_json_scalar(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, str):
        return bool(value)
    return isinstance(value, (int, float))


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _json_dumps(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
