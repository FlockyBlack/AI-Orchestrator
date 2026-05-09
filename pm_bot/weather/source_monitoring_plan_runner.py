from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

PLAN_CONTRACT_VERSION = "pmbot_weather_source_monitoring_plan.v1"
RUN_REPORT_CONTRACT_VERSION = "pmbot_weather_source_monitoring_run.v1"

LOCAL_RUN_MODE = "local_fixture_only"
RUNNER_STATE = "assembled_for_operator_review"
RUNNER_VERDICT = "not_evaluated"
OPERATOR_REVIEW_STATE = "pending_operator_review"

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
    }
)

NETWORK_PREFIXES = ("http://", "https://", "ws://", "wss://")

REQUIRED_SOURCE_FIELDS = frozenset(
    {
        "source_id",
        "label",
        "source_type",
        "local_reference",
        "snapshot_id",
        "observed_fields",
    }
)

REQUIRED_CHECK_FIELDS = frozenset(
    {
        "outcome_id",
        "title",
        "source_ids",
        "evidence_fields",
        "operator_review_steps",
    }
)

ALLOWED_TOP_LEVEL_FIELDS = frozenset(
    {
        "contract_version",
        "plan_id",
        "scope",
        "local_only",
        "operator_review_required",
        "market_context",
        "sources",
        "outcome_checks",
    }
)


@dataclass(frozen=True)
class PlanValidationResult:
    valid: bool
    errors: tuple[str, ...]


class PlanValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        super().__init__("weather source monitoring plan is invalid")
        self.errors = tuple(errors)


def load_plan(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise PlanValidationError(("plan JSON must be an object",))
    return data


def validate_plan(plan: Mapping[str, Any]) -> PlanValidationResult:
    errors: list[str] = []

    unknown_fields = sorted(set(plan) - ALLOWED_TOP_LEVEL_FIELDS)
    if unknown_fields:
        errors.append(f"unknown top-level fields: {', '.join(unknown_fields)}")

    missing_fields = sorted(ALLOWED_TOP_LEVEL_FIELDS - set(plan) - {"market_context"})
    if missing_fields:
        errors.append(f"missing required fields: {', '.join(missing_fields)}")

    if plan.get("contract_version") != PLAN_CONTRACT_VERSION:
        errors.append(f"contract_version must be {PLAN_CONTRACT_VERSION}")
    if plan.get("local_only") is not True:
        errors.append("local_only must be true")
    if plan.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")

    errors.extend(_find_forbidden_decision_fields(plan))

    sources = plan.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        sources = []
    source_ids = _validate_sources(sources, errors)

    outcome_checks = plan.get("outcome_checks")
    if not isinstance(outcome_checks, list) or not outcome_checks:
        errors.append("outcome_checks must be a non-empty list")
        outcome_checks = []
    _validate_outcome_checks(outcome_checks, source_ids, errors)

    return PlanValidationResult(valid=not errors, errors=tuple(errors))


def build_run_report(plan: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_plan(plan)
    if not validation.valid:
        raise PlanValidationError(validation.errors)

    plan_id = _string_field(plan, "plan_id")
    report = {
        "contract_version": RUN_REPORT_CONTRACT_VERSION,
        "run_id": _stable_run_id(plan),
        "plan_id": plan_id,
        "run_mode": LOCAL_RUN_MODE,
        "scope": _string_field(plan, "scope"),
        "local_only": True,
        "operator_review_required": True,
        "market_context": dict(plan.get("market_context") or {}),
        "summary_counts": {
            "sources": len(plan["sources"]),
            "monitoring_items": len(plan["outcome_checks"]),
        },
        "source_inventory": [_source_report(source) for source in plan["sources"]],
        "outcome_monitoring_items": [
            _outcome_check_report(outcome_check) for outcome_check in plan["outcome_checks"]
        ],
        "safety_boundaries": {
            "offline_inputs_only": True,
            "network_calls_allowed": False,
            "llm_calls_allowed": False,
            "external_market_api_allowed": False,
            "wallet_or_order_code_allowed": False,
            "runtime_wiring_allowed": False,
            "scheduler_or_worker_allowed": False,
            "trade_action_guidance_allowed": False,
            "operator_review_gate_required": True,
        },
        "warnings": [],
        "errors": [],
    }
    return report


def write_run_report(plan_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    plan = load_plan(plan_path)
    report = build_run_report(plan)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(_json_dumps(report), encoding="utf-8")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local PMBOT weather source monitoring plan.")
    parser.add_argument("--plan", required=True, help="Path to a local weather monitoring plan JSON file.")
    parser.add_argument("--output", required=True, help="Path where the local run report JSON will be written.")
    args = parser.parse_args(argv)

    try:
        write_run_report(args.plan, args.output)
    except PlanValidationError as exc:
        for error in exc.errors:
            print(f"error: {error}")
        return 1
    return 0


def _validate_sources(sources: Sequence[Any], errors: list[str]) -> set[str]:
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        path = f"sources[{index}]"
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

        observed_fields = source.get("observed_fields")
        if not _is_non_empty_string_list(observed_fields):
            errors.append(f"{path}.observed_fields must be a non-empty list of strings")

    return source_ids


def _validate_outcome_checks(
    outcome_checks: Sequence[Any],
    source_ids: set[str],
    errors: list[str],
) -> None:
    outcome_ids: set[str] = set()
    for index, outcome_check in enumerate(outcome_checks):
        path = f"outcome_checks[{index}]"
        if not isinstance(outcome_check, Mapping):
            errors.append(f"{path} must be an object")
            continue

        missing = sorted(REQUIRED_CHECK_FIELDS - set(outcome_check))
        if missing:
            errors.append(f"{path} missing required fields: {', '.join(missing)}")

        outcome_id = outcome_check.get("outcome_id")
        if not isinstance(outcome_id, str) or not outcome_id:
            errors.append(f"{path}.outcome_id must be a non-empty string")
        elif outcome_id in outcome_ids:
            errors.append(f"{path}.outcome_id must be unique")
        else:
            outcome_ids.add(outcome_id)

        check_source_ids = outcome_check.get("source_ids")
        if not _is_non_empty_string_list(check_source_ids):
            errors.append(f"{path}.source_ids must be a non-empty list of strings")
        else:
            missing_source_ids = sorted(set(check_source_ids) - source_ids)
            if missing_source_ids:
                errors.append(f"{path}.source_ids references unknown sources: {', '.join(missing_source_ids)}")

        evidence_fields = outcome_check.get("evidence_fields")
        if not _is_non_empty_string_list(evidence_fields):
            errors.append(f"{path}.evidence_fields must be a non-empty list of strings")

        operator_review_steps = outcome_check.get("operator_review_steps")
        if not _is_non_empty_string_list(operator_review_steps):
            errors.append(f"{path}.operator_review_steps must be a non-empty list of strings")


def _source_report(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source["source_id"],
        "label": source["label"],
        "source_type": source["source_type"],
        "local_reference": source["local_reference"],
        "snapshot_id": source["snapshot_id"],
        "observed_fields": list(source["observed_fields"]),
        "runner_state": RUNNER_STATE,
        "operator_review_status": OPERATOR_REVIEW_STATE,
    }


def _outcome_check_report(outcome_check: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "outcome_id": outcome_check["outcome_id"],
        "title": outcome_check["title"],
        "source_ids": list(outcome_check["source_ids"]),
        "evidence_fields": list(outcome_check["evidence_fields"]),
        "operator_review_steps": list(outcome_check["operator_review_steps"]),
        "runner_state": RUNNER_STATE,
        "runner_verdict": RUNNER_VERDICT,
        "operator_review_status": OPERATOR_REVIEW_STATE,
    }


def _stable_run_id(plan: Mapping[str, Any]) -> str:
    plan_id = _string_field(plan, "plan_id")
    digest = hashlib.sha256(_json_dumps(plan).encode("utf-8")).hexdigest()[:12]
    return f"{plan_id}-{digest}"


def _find_forbidden_decision_fields(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, Mapping):
        for raw_key, nested_value in value.items():
            key = str(raw_key)
            key_path = f"{path}.{key}"
            if _contains_forbidden_token(key):
                hits.append(f"forbidden decision/action field detected at {key_path}")
            hits.extend(_find_forbidden_decision_fields(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_forbidden_decision_fields(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _contains_forbidden_token(value):
        hits.append(f"forbidden decision/action text detected at {path}")
    return hits


def _contains_forbidden_token(value: str) -> bool:
    normalized = []
    for character in value.lower():
        normalized.append(character if character.isalnum() else "_")
    tokens = {token for token in "".join(normalized).split("_") if token}
    return bool(tokens & FORBIDDEN_DECISION_FIELD_TOKENS)


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _string_field(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise PlanValidationError((f"{key} must be a non-empty string",))
    return value


def _json_dumps(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
