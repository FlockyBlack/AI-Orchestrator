from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

REFRESH_REQUEST_CONTRACT_VERSION = "pmbot_weather_observation_ledger_refresh_request.v1"
OBSERVATION_LEDGER_CONTRACT_VERSION = "pmbot_weather_observation_ledger.v1"
SNAPSHOT_CONTRACT_VERSION = "pmbot_weather_observation_snapshot.v1"

LOCAL_RUN_MODE = "local_fixture_only"
LEDGER_RECORD_STATE = "refreshed_from_local_fixture"
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
    }
)

ALLOWED_TOP_LEVEL_FIELDS = frozenset(
    {
        "contract_version",
        "ledger_id",
        "scope",
        "local_only",
        "operator_review_required",
        "market_context",
        "source_snapshots",
        "record_specs",
        "operator_review_steps",
    }
)

REQUIRED_TOP_LEVEL_FIELDS = ALLOWED_TOP_LEVEL_FIELDS - {"market_context"}

REQUIRED_SOURCE_FIELDS = frozenset(
    {
        "source_id",
        "label",
        "source_type",
        "local_reference",
        "snapshot_id",
        "required_fields",
    }
)

REQUIRED_RECORD_SPEC_FIELDS = frozenset(
    {
        "record_id",
        "source_id",
        "measurement_name",
        "observation_date_field",
        "station_id_field",
        "value_field",
        "unit",
        "timestamp_field",
        "operator_review_label",
    }
)


@dataclass(frozen=True)
class LedgerRefreshValidationResult:
    valid: bool
    errors: tuple[str, ...]


class LedgerRefreshValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        super().__init__("weather observation ledger refresh request is invalid")
        self.errors = tuple(errors)


def load_refresh_request(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise LedgerRefreshValidationError(("refresh request JSON must be an object",))
    return data


def validate_refresh_request(request: Mapping[str, Any]) -> LedgerRefreshValidationResult:
    errors: list[str] = []

    unknown_fields = sorted(set(request) - ALLOWED_TOP_LEVEL_FIELDS)
    if unknown_fields:
        errors.append(f"unknown top-level fields: {', '.join(unknown_fields)}")

    missing_fields = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(request))
    if missing_fields:
        errors.append(f"missing required fields: {', '.join(missing_fields)}")

    if request.get("contract_version") != REFRESH_REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REFRESH_REQUEST_CONTRACT_VERSION}")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")

    errors.extend(_find_forbidden_decision_fields(request))

    source_snapshots = request.get("source_snapshots")
    if not isinstance(source_snapshots, list) or not source_snapshots:
        errors.append("source_snapshots must be a non-empty list")
        source_snapshots = []
    source_ids = _validate_source_snapshots(source_snapshots, errors)

    record_specs = request.get("record_specs")
    if not isinstance(record_specs, list) or not record_specs:
        errors.append("record_specs must be a non-empty list")
        record_specs = []
    _validate_record_specs(record_specs, source_ids, errors)

    operator_review_steps = request.get("operator_review_steps")
    if not _is_non_empty_string_list(operator_review_steps):
        errors.append("operator_review_steps must be a non-empty list of strings")

    return LedgerRefreshValidationResult(valid=not errors, errors=tuple(errors))


def build_observation_ledger(
    request: Mapping[str, Any],
    *,
    base_path: str | Path | None = None,
) -> dict[str, Any]:
    validation = validate_refresh_request(request)
    if not validation.valid:
        raise LedgerRefreshValidationError(validation.errors)

    root = Path.cwd() if base_path is None else Path(base_path)
    snapshots = _load_snapshots(request["source_snapshots"], root)
    source_by_id = {source["source_id"]: source for source in request["source_snapshots"]}
    snapshot_by_source_id = {snapshot["source_id"]: snapshot for snapshot in snapshots}
    records = [
        _build_ledger_record(
            record_spec,
            source_by_id[record_spec["source_id"]],
            snapshot_by_source_id[record_spec["source_id"]],
        )
        for record_spec in request["record_specs"]
    ]

    refresh_id = _stable_refresh_id(request, snapshots)
    return {
        "contract_version": OBSERVATION_LEDGER_CONTRACT_VERSION,
        "ledger_id": _string_field(request, "ledger_id"),
        "refresh_id": refresh_id,
        "run_mode": LOCAL_RUN_MODE,
        "scope": _string_field(request, "scope"),
        "local_only": True,
        "operator_review_required": True,
        "market_context": dict(request.get("market_context") or {}),
        "summary_counts": {
            "source_snapshots": len(snapshots),
            "ledger_records": len(records),
            "warnings": 0,
        },
        "source_inventory": [
            _source_inventory_entry(source, snapshot_by_source_id[source["source_id"]])
            for source in request["source_snapshots"]
        ],
        "records": records,
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
            "weather_outcome_evaluation_allowed": False,
            "operator_review_gate_required": True,
        },
        "warnings": [],
        "errors": [],
    }


def build_operator_report(ledger: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Weather Observation Ledger Refresh",
        "",
        f"- Contract: `{ledger['contract_version']}`",
        f"- Ledger: `{ledger['ledger_id']}`",
        f"- Refresh: `{ledger['refresh_id']}`",
        f"- Run mode: `{ledger['run_mode']}`",
        f"- Operator review: `{ledger['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Source snapshots: {ledger['summary_counts']['source_snapshots']}",
        f"- Ledger records: {ledger['summary_counts']['ledger_records']}",
        f"- Warnings: {ledger['summary_counts']['warnings']}",
        "",
        "## Records",
        "",
    ]

    for record in ledger["records"]:
        lines.append(
            "- "
            f"`{record['record_id']}`: {record['measurement_name']} = "
            f"{record['reported_value']} {record['unit']} from "
            f"`{record['source_id']}` field `{record['value_field']}`; "
            f"review `{record['operator_review_status']}`."
        )

    lines.extend(
        [
            "",
            "## Operator Review",
            "",
        ]
    )
    for step in ledger["operator_review"]["required_steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Uses local fixture/static inputs only.",
            "- Makes no network, LLM, market API, wallet, order, or runtime calls.",
            "- Produces observation ledger records for human review only.",
            "- Does not evaluate weather outcomes or provide trade action guidance.",
            "",
        ]
    )
    return "\n".join(lines)


def write_refresh_outputs(
    request_path: str | Path,
    output_ledger_path: str | Path,
    output_report_path: str | Path,
    *,
    base_path: str | Path | None = None,
) -> dict[str, Any]:
    request = load_refresh_request(request_path)
    ledger = build_observation_ledger(request, base_path=base_path)

    ledger_destination = Path(output_ledger_path)
    ledger_destination.parent.mkdir(parents=True, exist_ok=True)
    ledger_destination.write_text(_json_dumps(ledger), encoding="utf-8")

    report_destination = Path(output_report_path)
    report_destination.parent.mkdir(parents=True, exist_ok=True)
    report_destination.write_text(build_operator_report(ledger), encoding="utf-8")

    return ledger


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh a local PMBOT weather observation ledger.")
    parser.add_argument("--request", required=True, help="Path to a local ledger refresh request JSON file.")
    parser.add_argument(
        "--output-ledger",
        required=True,
        help="Path where the refreshed ledger JSON will be written.",
    )
    parser.add_argument(
        "--output-report",
        required=True,
        help="Path where the operator Markdown report will be written.",
    )
    args = parser.parse_args(argv)

    try:
        write_refresh_outputs(args.request, args.output_ledger, args.output_report)
    except LedgerRefreshValidationError as exc:
        for error in exc.errors:
            print(f"error: {error}")
        return 1
    return 0


def _validate_source_snapshots(source_snapshots: Sequence[Any], errors: list[str]) -> set[str]:
    source_ids: set[str] = set()
    for index, source in enumerate(source_snapshots):
        path = f"source_snapshots[{index}]"
        if not isinstance(source, Mapping):
            errors.append(f"{path} must be an object")
            continue

        missing = sorted(REQUIRED_SOURCE_FIELDS - set(source))
        if missing:
            errors.append(f"{path} missing required fields: {', '.join(missing)}")

        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{path}.source_id must be a non-empty string")
        elif source_id in source_ids:
            errors.append(f"{path}.source_id must be unique")
        else:
            source_ids.add(source_id)

        local_reference = source.get("local_reference")
        if not isinstance(local_reference, str) or not local_reference:
            errors.append(f"{path}.local_reference must be a non-empty string")
        elif local_reference.lower().startswith(NETWORK_PREFIXES):
            errors.append(f"{path}.local_reference must point to a local fixture or static artifact")
        elif not _is_allowed_local_reference(local_reference):
            errors.append(f"{path}.local_reference must stay under an allowed local fixture/static path")

        required_fields = source.get("required_fields")
        if not _is_non_empty_string_list(required_fields):
            errors.append(f"{path}.required_fields must be a non-empty list of strings")

    return source_ids


def _validate_record_specs(
    record_specs: Sequence[Any],
    source_ids: set[str],
    errors: list[str],
) -> None:
    record_ids: set[str] = set()
    for index, record_spec in enumerate(record_specs):
        path = f"record_specs[{index}]"
        if not isinstance(record_spec, Mapping):
            errors.append(f"{path} must be an object")
            continue

        missing = sorted(REQUIRED_RECORD_SPEC_FIELDS - set(record_spec))
        if missing:
            errors.append(f"{path} missing required fields: {', '.join(missing)}")

        for field in REQUIRED_RECORD_SPEC_FIELDS:
            value = record_spec.get(field)
            if not isinstance(value, str) or not value:
                errors.append(f"{path}.{field} must be a non-empty string")

        record_id = record_spec.get("record_id")
        if isinstance(record_id, str) and record_id:
            if record_id in record_ids:
                errors.append(f"{path}.record_id must be unique")
            else:
                record_ids.add(record_id)

        source_id = record_spec.get("source_id")
        if isinstance(source_id, str) and source_id and source_id not in source_ids:
            errors.append(f"{path}.source_id references unknown source: {source_id}")


def _load_snapshots(source_snapshots: Sequence[Mapping[str, Any]], root: Path) -> list[dict[str, Any]]:
    errors: list[str] = []
    snapshots: list[dict[str, Any]] = []
    for index, source in enumerate(source_snapshots):
        path = f"source_snapshots[{index}]"
        reference = source["local_reference"]
        local_path = root / Path(reference)

        try:
            with local_path.open("r", encoding="utf-8") as handle:
                snapshot = json.load(handle)
        except FileNotFoundError:
            errors.append(f"{path}.local_reference does not exist: {reference}")
            continue
        except json.JSONDecodeError as exc:
            errors.append(f"{path}.local_reference is not valid JSON: {exc.msg}")
            continue

        if not isinstance(snapshot, dict):
            errors.append(f"{path}.local_reference must contain a JSON object")
            continue

        if snapshot.get("contract_version") != SNAPSHOT_CONTRACT_VERSION:
            errors.append(f"{path}.local_reference contract_version must be {SNAPSHOT_CONTRACT_VERSION}")
        if snapshot.get("source_id") != source["source_id"]:
            errors.append(f"{path}.local_reference source_id must match request source_id")
        if snapshot.get("source_type") != source["source_type"]:
            errors.append(f"{path}.local_reference source_type must match request source_type")
        if snapshot.get("snapshot_id") != source["snapshot_id"]:
            errors.append(f"{path}.local_reference snapshot_id must match request snapshot_id")

        missing_fields = sorted(field for field in source["required_fields"] if field not in snapshot)
        if missing_fields:
            errors.append(f"{path}.local_reference missing required fields: {', '.join(missing_fields)}")

        snapshots.append(snapshot)

    if errors:
        raise LedgerRefreshValidationError(errors)
    return snapshots


def _build_ledger_record(
    record_spec: Mapping[str, Any],
    source: Mapping[str, Any],
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    required_snapshot_fields = [
        record_spec["observation_date_field"],
        record_spec["station_id_field"],
        record_spec["value_field"],
        record_spec["timestamp_field"],
    ]
    missing_fields = [field for field in required_snapshot_fields if field not in snapshot]
    if missing_fields:
        raise LedgerRefreshValidationError(
            (
                f"record_specs record_id {record_spec['record_id']} references missing snapshot fields: "
                f"{', '.join(sorted(missing_fields))}",
            )
        )

    return {
        "record_id": record_spec["record_id"],
        "source_id": source["source_id"],
        "source_label": source["label"],
        "source_type": source["source_type"],
        "local_reference": source["local_reference"],
        "snapshot_id": source["snapshot_id"],
        "observation_date": snapshot[record_spec["observation_date_field"]],
        "station_id": snapshot[record_spec["station_id_field"]],
        "measurement_name": record_spec["measurement_name"],
        "value_field": record_spec["value_field"],
        "reported_value": snapshot[record_spec["value_field"]],
        "unit": record_spec["unit"],
        "source_timestamp": snapshot[record_spec["timestamp_field"]],
        "operator_review_label": record_spec["operator_review_label"],
        "runner_state": LEDGER_RECORD_STATE,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
    }


def _source_inventory_entry(source: Mapping[str, Any], snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source["source_id"],
        "label": source["label"],
        "source_type": source["source_type"],
        "local_reference": source["local_reference"],
        "snapshot_id": source["snapshot_id"],
        "required_fields": list(source["required_fields"]),
        "snapshot_loaded": True,
        "observation_date": snapshot.get("observation_date"),
        "station_id": snapshot.get("station_id"),
        "runner_state": LEDGER_RECORD_STATE,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
    }


def _stable_refresh_id(request: Mapping[str, Any], snapshots: Sequence[Mapping[str, Any]]) -> str:
    ledger_id = _string_field(request, "ledger_id")
    material = {"request": request, "snapshots": list(snapshots)}
    digest = hashlib.sha256(_json_dumps(material).encode("utf-8")).hexdigest()[:12]
    return f"{ledger_id}-{digest}"


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


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _string_field(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise LedgerRefreshValidationError((f"{key} must be a non-empty string",))
    return value


def _json_dumps(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
