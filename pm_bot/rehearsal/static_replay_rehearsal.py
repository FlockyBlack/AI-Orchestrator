from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


RESULT_CONTRACT_VERSION = "pmbot_actual_read_only_rehearsal_static_replay_result.v1"
FAILURE_MODE_RESULT_CONTRACT_VERSION = (
    "pmbot_actual_read_only_rehearsal_static_replay_failure_modes.v1"
)
MARKET_PACKET_CONTRACT_VERSION = "pmbot_actual_read_only_rehearsal_market_packet.v1"
REHEARSAL_MODE = "static_replay"
FAILURE_MODE_REHEARSAL_MODE = "static_replay_failure_modes"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
DEFAULT_RESULT_PATH = "pm_bot/rehearsal/artifacts/actual_static_replay_rehearsal_001.result.json"
DEFAULT_MARKDOWN_PATH = "pm_bot/rehearsal/artifacts/actual_static_replay_rehearsal_001.md"
DEFAULT_LINK_MAP_PATH = (
    "pm_bot/rehearsal/artifacts/actual_static_replay_rehearsal_001.operator_surface_link_map.json"
)
DEFAULT_FAILURE_MODE_RESULT_PATH = (
    "pm_bot/rehearsal/artifacts/actual_static_replay_failure_modes_002.result.json"
)
DEFAULT_FAILURE_MODE_MARKDOWN_PATH = (
    "pm_bot/rehearsal/artifacts/actual_static_replay_failure_modes_002.md"
)
FAILURE_MODE_BATCH_ID = "actual_static_replay_failure_modes_002"

REQUIRED_MARKET_PACKET_FIELDS = (
    "contract_version",
    "local_only",
    "market_packet_id",
    "mode",
    "operator_review_status",
    "rehearsal_id",
    "required_evidence_ids",
    "safety_boundaries",
    "static_source_ids",
)
REQUIRED_SOURCE_EVIDENCE_FIELDS = (
    "bundle_id",
    "contract_version",
    "linked_market_packet_id",
    "local_only",
    "operator_review_status",
    "rehearsal_id",
    "safety_boundaries",
    "source_evidence_records",
)
REQUIRED_STALENESS_CASE_FIELDS = (
    "case_id",
    "evidence_id",
    "maximum_age_seconds",
    "observed_timestamp_utc",
    "reference_timestamp_utc",
    "severity_if_stale",
    "timestamp_field_present",
    "timestamp_required",
)
REQUIRED_CONTRADICTION_CASE_FIELDS = (
    "case_id",
    "left_evidence_id",
    "left_field_present",
    "left_static_value",
    "right_evidence_id",
    "right_field_present",
    "right_static_value",
    "semantic_field",
    "severity_if_detected",
    "subject_keys_match",
    "values_match",
)
REQUIRED_STOP_CONDITION_FIELDS = (
    "condition_id",
    "enabled",
    "severity",
    "status_key",
    "trigger_on_statuses",
    "trigger_state_after_match",
)

ALLOWED_LOCAL_REFERENCE_PREFIXES = (
    "docs/",
    "pm_bot/dashboard/",
    "pm_bot/paper_accounting/",
    "pm_bot/rehearsal/",
    "pm_bot/simulated_decisions/",
    "pm_bot/source_quality/",
    "pm_bot/tests/",
    "tests/",
)
FORBIDDEN_REFERENCE_PREFIXES = (
    ".codex/",
    ".env",
    ".env.",
    ".git/",
    "pm_bot/llm/",
    "pm_bot/orders/",
    "pm_bot/trading/",
    "pm_bot/wallet/",
    "run_codex/",
    "runtime/",
)
SENSITIVE_PATH_PARTS = {
    ".env",
    ".git",
    "auth",
    "browser profiles",
    "credential",
    "credentials",
    "key",
    "keys",
    "private",
    "secret",
    "secrets",
    "seed",
    "signing",
    "wallet",
}
TRUE_SAFETY_BOUNDARIES = {
    "local_only",
    "local_static_samples_only",
    "operator_review_required",
    "paper_mode_only",
}
FORBIDDEN_ACTION_TEXT_TOKENS = {
    "buy",
    "enter",
    "exit",
    "hold",
    "pick",
    "sell",
    "stake",
    "wager",
}
SENSITIVE_TEXT_MARKERS = (
    ".env",
    "api_key",
    "auth token",
    "browser profile",
    "credential",
    "private key",
    "private_key",
    "secret",
    "seed phrase",
    "signing key",
    "wallet",
)
SAFETY_SCAN_SKIP_KEYS = {"excluded_fields", "safety_boundaries"}
STATIC_REPLAY_INPUT_FILENAMES = {
    "contradiction_case_set_path": "contradiction_case_set.json",
    "market_packet_path": "market_packet.json",
    "source_evidence_path": "source_evidence.json",
    "staleness_case_set_path": "staleness_case_set.json",
    "stop_condition_matrix_path": "stop_condition_matrix.json",
}
SAFE_RESULT_FLAGS = {
    "authenticated_endpoints_used": False,
    "live_network_used": False,
    "market_recommendation_generated": False,
    "openrouter_calls_performed": 0,
    "orders_or_trading_actions": False,
    "polymarket_api_calls_performed": 0,
    "probability_ev_edge_or_side_selection_generated": False,
    "runtime_or_dispatcher_changes": False,
    "wallet_or_private_key_access": False,
}


class StaticReplayRehearsalError(ValueError):
    """Raised when a local static replay rehearsal cannot be loaded."""


def run_static_replay_rehearsal(
    *,
    market_packet_path: str | Path,
    source_evidence_path: str | Path,
    staleness_case_set_path: str | Path | None = None,
    contradiction_case_set_path: str | Path | None = None,
    stop_condition_matrix_path: str | Path | None = None,
    generated_artifact_paths: Mapping[str, str] | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Run a deterministic local static replay rehearsal from saved packet files."""

    root = _repo_root(repo_root)
    artifact_paths = {
        "operator_surface_link_map": DEFAULT_LINK_MAP_PATH,
        "rehearsal_result_json": DEFAULT_RESULT_PATH,
        "rehearsal_summary_markdown": DEFAULT_MARKDOWN_PATH,
    }
    if generated_artifact_paths:
        artifact_paths.update(dict(generated_artifact_paths))

    market_packet = _load_json_object(_resolve_input_path(market_packet_path))
    source_evidence = _load_json_object(_resolve_input_path(source_evidence_path))
    staleness_case_set = (
        _load_json_object(_resolve_input_path(staleness_case_set_path))
        if staleness_case_set_path is not None
        else None
    )
    contradiction_case_set = (
        _load_json_object(_resolve_input_path(contradiction_case_set_path))
        if contradiction_case_set_path is not None
        else None
    )
    stop_condition_matrix = (
        _load_json_object(_resolve_input_path(stop_condition_matrix_path))
        if stop_condition_matrix_path is not None
        else None
    )

    warnings: list[str] = []
    hard_blockers: list[str] = []

    market_errors = _validate_market_packet(market_packet)
    source_status = _check_source_evidence(root, market_packet, source_evidence)
    staleness_status = _check_staleness_cases(staleness_case_set)
    contradiction_status = _check_contradiction_cases(contradiction_case_set)
    input_safety_status = _check_input_safety_text(
        {
            "contradiction_case_set": contradiction_case_set,
            "market_packet": market_packet,
            "source_evidence": source_evidence,
            "staleness_case_set": staleness_case_set,
            "stop_condition_matrix": stop_condition_matrix,
        }
    )

    hard_blockers.extend(f"market_packet:{error}" for error in market_errors)
    hard_blockers.extend(f"source_evidence:{error}" for error in source_status["errors"])
    hard_blockers.extend(
        f"staleness:{case_id}" for case_id in staleness_status["hard_blocker_case_ids"]
    )
    hard_blockers.extend(
        f"contradiction:{case_id}" for case_id in contradiction_status["hard_blocker_case_ids"]
    )
    hard_blockers.extend(input_safety_status["hard_blockers"])
    warnings.extend(staleness_status["warnings"])
    warnings.extend(contradiction_status["warnings"])
    warnings.extend(input_safety_status["warnings"])

    base_status_context = {
        "contradiction_check_status": contradiction_status["status"],
        "market_packet_status": "failed" if market_errors else "passed",
        "source_evidence_status": source_status["status"],
        "staleness_check_status": staleness_status["status"],
    }
    stop_status = _apply_stop_condition_matrix(stop_condition_matrix, base_status_context)
    hard_blockers.extend(f"stop_condition:{condition_id}" for condition_id in stop_status["hard_blocker_condition_ids"])
    warnings.extend(stop_status["warnings"])

    rehearsal_passed = (
        not hard_blockers
        and source_status["status"] == "passed"
        and staleness_status["status"] == "passed"
        and contradiction_status["status"] == "passed"
        and stop_status["status"] == "passed"
    )

    result = {
        "authenticated_endpoints_used": False,
        "contract_version": RESULT_CONTRACT_VERSION,
        "contradiction_check_status": contradiction_status,
        "generated_artifacts": dict(sorted(artifact_paths.items())),
        "hard_blockers": sorted(hard_blockers),
        "input_artifacts": {
            "contradiction_case_set": _normalize_optional_path(contradiction_case_set_path),
            "market_packet": _normalize_path_string(market_packet_path),
            "source_evidence": _normalize_path_string(source_evidence_path),
            "staleness_case_set": _normalize_optional_path(staleness_case_set_path),
            "stop_condition_matrix": _normalize_optional_path(stop_condition_matrix_path),
        },
        "live_network_used": False,
        "market_recommendation_generated": False,
        "mode": REHEARSAL_MODE,
        "next_allowed_actions": [
            "operator review of local run artifacts",
            "controlled static replay failure-mode hardening",
            "controlled public read-only fetch preparation only after a separate approval task",
        ],
        "openrouter_calls_performed": 0,
        "operator_approval_granted": False,
        "operator_approval_required": True,
        "orders_or_trading_actions": False,
        "polymarket_api_calls_performed": 0,
        "probability_ev_edge_or_side_selection_generated": False,
        "rehearsal_id": str(market_packet.get("rehearsal_id", "unknown_rehearsal_id")),
        "rehearsal_passed": rehearsal_passed,
        "source_evidence_status": source_status,
        "staleness_check_status": staleness_status,
        "stop_condition_status": stop_status,
        "wallet_or_private_key_access": False,
        "warnings": sorted(set(warnings)),
    }
    if input_safety_status["status"] != "passed":
        result["input_safety_status"] = input_safety_status
    return result


def build_operator_surface_link_map(result: Mapping[str, Any]) -> dict[str, Any]:
    rehearsal_id = str(result["rehearsal_id"])
    surface_links = [
        {
            "local_reference": "pm_bot/dashboard/local_rehearsal_readiness_dashboard_card.py",
            "surface_id": "rehearsal_readiness_dashboard_card",
            "surface_role": "operator_readiness_review",
        },
        {
            "local_reference": "docs/PMBOT_REHEARSAL_012_REHEARSAL_MORNING_OPERATOR_CARD_LOCAL_ONLY.md",
            "surface_id": "rehearsal_morning_operator_card",
            "surface_role": "morning_operator_review",
        },
        {
            "local_reference": "docs/PMBOT_REHEARSAL_013_REHEARSAL_ACCEPTANCE_REPORT_LOCAL_ONLY.md",
            "surface_id": "rehearsal_acceptance_report",
            "surface_role": "acceptance_review",
        },
        {
            "local_reference": "pm_bot/source_quality/rehearsal_source_quality_links.py",
            "surface_id": "rehearsal_source_quality_links",
            "surface_role": "source_quality_review",
        },
        {
            "local_reference": "pm_bot/paper_accounting/rehearsal_paperlive_accounting_links.py",
            "surface_id": "rehearsal_paperlive_accounting_links",
            "surface_role": "paperlive_accounting_reference",
        },
        {
            "local_reference": "pm_bot/simulated_decisions/rehearsal_simulated_decision_replay_links.py",
            "surface_id": "rehearsal_simulated_decision_replay_links",
            "surface_role": "simulated_replay_reference",
        },
    ]
    return {
        "contract_version": "pmbot_actual_read_only_rehearsal_operator_surface_link_map.v1",
        "live_network_used": False,
        "local_only": True,
        "operator_approval_required": True,
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "rehearsal_id": rehearsal_id,
        "rehearsal_result_reference": result["generated_artifacts"]["rehearsal_result_json"],
        "surface_links": surface_links,
        "summary_counts": {
            "surface_links": len(surface_links),
            "warnings": 0,
        },
        "warnings": [],
    }


def render_markdown_summary(result: Mapping[str, Any]) -> str:
    blockers = result["hard_blockers"] or ["none"]
    warnings = result["warnings"] or ["none"]
    allowed_next = result["next_allowed_actions"]
    still_blocked = [
        "live network access",
        "OpenRouter calls",
        "Polymarket API calls",
        "authenticated endpoint use",
        "wallet or private-key access",
        "order or trading action paths",
        "runtime or dispatcher changes",
        "autonomous trading readiness claims",
    ]

    lines = [
        "# Actual Read-Only Supervised-Live Rehearsal 001",
        "",
        "This was actual read-only supervised-live rehearsal #1.",
        "",
        f"Rehearsal ID: `{result['rehearsal_id']}`",
        "Mode: static/replayed source packets.",
        "Live network used: false.",
        "OpenRouter calls performed: 0.",
        "Polymarket API calls performed: 0.",
        "Authenticated endpoints used: false.",
        "Wallet/private-key access: false.",
        "Order or trading actions: false.",
        "",
        f"Rehearsal passed: {str(result['rehearsal_passed']).lower()}.",
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in blockers],
        "",
        "## Warnings",
        "",
        *[f"- {item}" for item in warnings],
        "",
        "## Allowed Next",
        "",
        *[f"- {item}" for item in allowed_next],
        "",
        "## Still Blocked",
        "",
        *[f"- {item}" for item in still_blocked],
        "",
        "This artifact is local-only, deterministic, and pending operator review.",
    ]
    return "\n".join(lines) + "\n"


def run_static_replay_failure_mode_batch(
    *,
    fixture_root: str | Path,
    generated_artifact_paths: Mapping[str, str] | None = None,
    base_rehearsal_id: str = "actual_static_replay_rehearsal_001",
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Run deterministic local failure-mode scenarios and summarize expectation checks."""

    root = Path(fixture_root)
    if not root.exists():
        raise StaticReplayRehearsalError(f"missing failure-mode fixture root: {_normalize_path_string(root)}")

    artifact_paths = {
        "failure_mode_result_json": DEFAULT_FAILURE_MODE_RESULT_PATH,
        "failure_mode_summary_markdown": DEFAULT_FAILURE_MODE_MARKDOWN_PATH,
    }
    if generated_artifact_paths:
        artifact_paths.update(dict(generated_artifact_paths))

    scenarios: list[dict[str, Any]] = []
    aggregated_hard_blockers: list[str] = []
    aggregated_warnings: list[str] = []

    for scenario_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        expected_behavior = _load_json_object(scenario_dir / "expected_behavior.json")
        result = run_static_replay_rehearsal(
            **_scenario_input_paths(scenario_dir),
            repo_root=repo_root,
        )
        expectation_failures = _scenario_expectation_failures(result, expected_behavior)
        passed = not expectation_failures
        aggregated_hard_blockers.extend(result["hard_blockers"])
        aggregated_warnings.extend(result["warnings"])
        scenarios.append(
            {
                "blockers": result["hard_blockers"],
                "expected_behavior": expected_behavior["expected_behavior"],
                "expectation_failures": expectation_failures,
                "fixture_dir": _normalize_path_string(scenario_dir),
                "input_artifacts": result["input_artifacts"],
                "observed_behavior": _summarize_failure_mode_observation(result),
                "pass": passed,
                "safety_notes": expected_behavior.get("safety_notes", []),
                "scenario_name": expected_behavior.get("scenario_name", scenario_dir.name),
                "warnings": result["warnings"],
            }
        )

    passed_scenario_count = sum(1 for scenario in scenarios if scenario["pass"] is True)
    failed_scenario_count = len(scenarios) - passed_scenario_count
    return {
        "all_failure_modes_behaved_as_expected": failed_scenario_count == 0,
        "authenticated_endpoints_used": False,
        "base_rehearsal_id": base_rehearsal_id,
        "contract_version": FAILURE_MODE_RESULT_CONTRACT_VERSION,
        "failed_scenario_count": failed_scenario_count,
        "generated_artifacts": dict(sorted(artifact_paths.items())),
        "hard_blockers": sorted(set(aggregated_hard_blockers)),
        "live_network_used": False,
        "market_recommendation_generated": False,
        "mode": FAILURE_MODE_REHEARSAL_MODE,
        "next_allowed_actions": [
            "operator review of local failure-mode replay artifacts",
            "controlled public read-only fetch preparation only after separate operator approval",
        ],
        "next_blocked_actions": [
            "live network access",
            "OpenRouter calls",
            "Polymarket API calls",
            "authenticated endpoint use",
            "wallet or private-key access",
            "order or trading action paths",
            "runtime or dispatcher changes",
            "autonomous trading readiness claims",
        ],
        "openrouter_calls_performed": 0,
        "orders_or_trading_actions": False,
        "passed_scenario_count": passed_scenario_count,
        "polymarket_api_calls_performed": 0,
        "probability_ev_edge_or_side_selection_generated": False,
        "rehearsal_failure_mode_batch_id": FAILURE_MODE_BATCH_ID,
        "runtime_or_dispatcher_changes": False,
        "scenarios": scenarios,
        "wallet_or_private_key_access": False,
        "warnings": sorted(set(aggregated_warnings)),
    }


def render_failure_mode_markdown_summary(batch_result: Mapping[str, Any]) -> str:
    lines = [
        "# Actual Static Replay Failure Modes 002",
        "",
        f"Batch: `{batch_result['rehearsal_failure_mode_batch_id']}`",
        f"Base rehearsal: `{batch_result['base_rehearsal_id']}`",
        "Mode: static replay failure modes.",
        "Live network used: false.",
        "OpenRouter calls performed: 0.",
        "Polymarket API calls performed: 0.",
        "Authenticated endpoints used: false.",
        "Wallet/private-key access: false.",
        "Order or trading actions: false.",
        "Runtime or dispatcher changes: false.",
        "",
        f"All failure modes behaved as expected: {str(batch_result['all_failure_modes_behaved_as_expected']).lower()}.",
        f"Passed scenarios: {batch_result['passed_scenario_count']}.",
        f"Failed scenarios: {batch_result['failed_scenario_count']}.",
        "",
    ]
    for scenario in batch_result["scenarios"]:
        lines.extend(
            [
                f"## {scenario['scenario_name']}",
                "",
                f"Expected behavior: {scenario['expected_behavior']}",
                f"Observed behavior: {scenario['observed_behavior']['summary']}",
                f"Pass/fail: {'pass' if scenario['pass'] else 'fail'}",
                "",
                "Blockers:",
                *[f"- {item}" for item in (scenario["blockers"] or ["none"])],
                "",
                "Warnings:",
                *[f"- {item}" for item in (scenario["warnings"] or ["none"])],
                "",
                "Safety notes:",
                *[f"- {item}" for item in (scenario["safety_notes"] or ["none"])],
                "",
            ]
        )
    lines.extend(
        [
            "## Still Blocked",
            "",
            *[f"- {item}" for item in batch_result["next_blocked_actions"]],
            "",
            "This artifact is local-only, deterministic, and pending operator review.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: str | Path, markdown: str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(markdown, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local-only PMBOT static replay rehearsal.")
    parser.add_argument("--market-packet", required=True)
    parser.add_argument("--source-evidence", required=True)
    parser.add_argument("--staleness-case-set")
    parser.add_argument("--contradiction-case-set")
    parser.add_argument("--stop-condition-matrix")
    parser.add_argument("--out", default=DEFAULT_RESULT_PATH)
    parser.add_argument("--markdown-out", default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--link-map-out", default=DEFAULT_LINK_MAP_PATH)
    args = parser.parse_args(argv)

    generated_paths = {
        "operator_surface_link_map": _normalize_path_string(args.link_map_out),
        "rehearsal_result_json": _normalize_path_string(args.out),
        "rehearsal_summary_markdown": _normalize_path_string(args.markdown_out),
    }
    result = run_static_replay_rehearsal(
        market_packet_path=args.market_packet,
        source_evidence_path=args.source_evidence,
        staleness_case_set_path=args.staleness_case_set,
        contradiction_case_set_path=args.contradiction_case_set,
        stop_condition_matrix_path=args.stop_condition_matrix,
        generated_artifact_paths=generated_paths,
    )
    link_map = build_operator_surface_link_map(result)

    write_json(args.out, result)
    write_markdown(args.markdown_out, render_markdown_summary(result))
    write_json(args.link_map_out, link_map)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["rehearsal_passed"] else 2


def _validate_market_packet(market_packet: Mapping[str, Any]) -> list[str]:
    errors = _missing_fields(market_packet, REQUIRED_MARKET_PACKET_FIELDS, "market_packet")
    if market_packet.get("contract_version") != MARKET_PACKET_CONTRACT_VERSION:
        errors.append(f"market_packet.contract_version must be {MARKET_PACKET_CONTRACT_VERSION}")
    if market_packet.get("mode") != REHEARSAL_MODE:
        errors.append("market_packet.mode must be static_replay")
    if market_packet.get("local_only") is not True:
        errors.append("market_packet.local_only must be true")
    if market_packet.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append("market_packet.operator_review_status must remain pending_operator_review")
    if not _is_non_empty_string_list(market_packet.get("required_evidence_ids")):
        errors.append("market_packet.required_evidence_ids must be a non-empty list of strings")
    if not _is_non_empty_string_list(market_packet.get("static_source_ids")):
        errors.append("market_packet.static_source_ids must be a non-empty list of strings")
    errors.extend(_safety_boundary_errors(market_packet.get("safety_boundaries"), "market_packet.safety_boundaries"))
    return errors


def _check_input_safety_text(payloads: Mapping[str, Any]) -> dict[str, Any]:
    forbidden_locations: list[str] = []
    sensitive_locations: list[str] = []
    for label, payload in payloads.items():
        if payload is None:
            continue
        _collect_input_safety_text_findings(
            payload,
            label,
            forbidden_locations=forbidden_locations,
            sensitive_locations=sensitive_locations,
        )

    hard_blockers: list[str] = []
    warnings: list[str] = []
    sanitized_findings: list[dict[str, Any]] = []
    if forbidden_locations:
        hard_blockers.append("safety:forbidden_action_text_sanitized")
        warnings.append("safety_sanitized_forbidden_action_text")
        sanitized_findings.append(
            {
                "category": "forbidden_action_text",
                "location_count": len(set(forbidden_locations)),
                "locations": sorted(set(forbidden_locations)),
            }
        )
    if sensitive_locations:
        hard_blockers.append("safety:sensitive_text_sanitized")
        warnings.append("safety_sanitized_sensitive_text")
        sanitized_findings.append(
            {
                "category": "sensitive_text",
                "location_count": len(set(sensitive_locations)),
                "locations": sorted(set(sensitive_locations)),
            }
        )

    return {
        "hard_blockers": sorted(hard_blockers),
        "sanitized_findings": sanitized_findings,
        "status": "blocked" if hard_blockers else "passed",
        "warnings": sorted(warnings),
    }


def _collect_input_safety_text_findings(
    value: Any,
    path: str,
    *,
    forbidden_locations: list[str],
    sensitive_locations: list[str],
) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_string = str(key)
            if key_string in SAFETY_SCAN_SKIP_KEYS:
                continue
            _collect_input_safety_text_findings(
                nested,
                f"{path}.{key_string}",
                forbidden_locations=forbidden_locations,
                sensitive_locations=sensitive_locations,
            )
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _collect_input_safety_text_findings(
                nested,
                f"{path}[{index}]",
                forbidden_locations=forbidden_locations,
                sensitive_locations=sensitive_locations,
            )
    elif isinstance(value, str):
        if _has_forbidden_action_text(value):
            forbidden_locations.append(path)
        if _has_sensitive_text_marker(value):
            sensitive_locations.append(path)


def _scenario_input_paths(scenario_dir: Path) -> dict[str, Path]:
    return {
        argument_name: scenario_dir / filename
        for argument_name, filename in STATIC_REPLAY_INPUT_FILENAMES.items()
    }


def _scenario_expectation_failures(
    result: Mapping[str, Any],
    expected_behavior: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    expected_passed = expected_behavior.get("expected_rehearsal_passed")
    if expected_passed is not None and result["rehearsal_passed"] is not expected_passed:
        failures.append(
            f"expected rehearsal_passed={str(expected_passed).lower()} "
            f"observed={str(result['rehearsal_passed']).lower()}"
        )

    for blocker_fragment in expected_behavior.get("expected_hard_blocker_fragments", []):
        if not any(str(blocker_fragment) in blocker for blocker in result["hard_blockers"]):
            failures.append(f"missing hard blocker fragment: {blocker_fragment}")

    for warning_fragment in expected_behavior.get("expected_warning_fragments", []):
        if not any(str(warning_fragment) in warning for warning in result["warnings"]):
            failures.append(f"missing warning fragment: {warning_fragment}")

    for status_key, expected_status in expected_behavior.get("expected_statuses", {}).items():
        observed_payload = result.get(status_key)
        observed_status = observed_payload.get("status") if isinstance(observed_payload, Mapping) else observed_payload
        if observed_status != expected_status:
            failures.append(f"expected {status_key}.status={expected_status} observed={observed_status}")

    default_safety_flags = {
        field_name: expected_value
        for field_name, expected_value in SAFE_RESULT_FLAGS.items()
        if field_name != "runtime_or_dispatcher_changes"
    }
    for field_name, expected_value in expected_behavior.get("expected_safety_flags", default_safety_flags).items():
        if result.get(field_name) != expected_value:
            failures.append(f"expected {field_name}={expected_value!r} observed={result.get(field_name)!r}")

    if expected_behavior.get("expected_no_action_text_leakage") is True and _contains_forbidden_action_text(result):
        failures.append("action-like input text leaked into result strings")
    if expected_behavior.get("expected_no_sensitive_text_leakage") is True and _contains_sensitive_text_marker(result):
        failures.append("sensitive-looking input text leaked into result strings")
    return failures


def _summarize_failure_mode_observation(result: Mapping[str, Any]) -> dict[str, Any]:
    status_summary = {
        "contradiction_check_status": result["contradiction_check_status"]["status"],
        "market_packet_status": "failed"
        if any(blocker.startswith("market_packet:") for blocker in result["hard_blockers"])
        else "passed",
        "source_evidence_status": result["source_evidence_status"]["status"],
        "staleness_check_status": result["staleness_check_status"]["status"],
        "stop_condition_status": result["stop_condition_status"]["status"],
    }
    if "input_safety_status" in result:
        status_summary["input_safety_status"] = result["input_safety_status"]["status"]

    return {
        "hard_blocker_count": len(result["hard_blockers"]),
        "rehearsal_passed": result["rehearsal_passed"],
        "status_summary": status_summary,
        "summary": _failure_mode_summary_sentence(result, status_summary),
        "warning_count": len(result["warnings"]),
    }


def _failure_mode_summary_sentence(result: Mapping[str, Any], status_summary: Mapping[str, str]) -> str:
    blocked_statuses = [
        f"{key}={status}"
        for key, status in status_summary.items()
        if status in {"blocked", "failed", "warning"}
    ]
    if not blocked_statuses and result["rehearsal_passed"]:
        return "scenario unexpectedly passed without blockers"
    if not blocked_statuses:
        return "scenario failed through explicit hard blockers"
    return "scenario failed safely with " + ", ".join(blocked_statuses)


def _check_source_evidence(
    repo_root: Path,
    market_packet: Mapping[str, Any],
    source_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    errors = _missing_fields(source_evidence, REQUIRED_SOURCE_EVIDENCE_FIELDS, "source_evidence")
    warnings: list[str] = []

    if source_evidence.get("local_only") is not True:
        errors.append("source_evidence.local_only must be true")
    if source_evidence.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append("source_evidence.operator_review_status must remain pending_operator_review")
    if source_evidence.get("rehearsal_id") != market_packet.get("rehearsal_id"):
        errors.append("source_evidence.rehearsal_id must match market_packet.rehearsal_id")
    if source_evidence.get("linked_market_packet_id") != market_packet.get("market_packet_id"):
        errors.append("source_evidence.linked_market_packet_id must match market_packet.market_packet_id")
    errors.extend(_safety_boundary_errors(source_evidence.get("safety_boundaries"), "source_evidence.safety_boundaries"))

    evidence_records = source_evidence.get("source_evidence_records")
    if not isinstance(evidence_records, list):
        errors.append("source_evidence.source_evidence_records must be a list")
        evidence_records = []

    required_ids = set(market_packet.get("required_evidence_ids") or [])
    source_ids = set(market_packet.get("static_source_ids") or [])
    present_ids: set[str] = set()
    checked_references: list[str] = []
    for index, record in enumerate(evidence_records):
        if not isinstance(record, Mapping):
            errors.append(f"source_evidence.source_evidence_records[{index}] must be an object")
            continue
        for field in ("evidence_id", "local_reference", "operator_review_status", "source_id"):
            if field not in record:
                errors.append(f"source_evidence.source_evidence_records[{index}].{field} is required")
        if record.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"source_evidence.source_evidence_records[{index}].operator_review_status must remain pending")
        evidence_id = record.get("evidence_id")
        if isinstance(evidence_id, str):
            present_ids.add(evidence_id)
        source_id = record.get("source_id")
        if isinstance(source_id, str) and source_ids and source_id not in source_ids:
            errors.append(f"source_evidence.source_evidence_records[{index}].source_id is not declared by market packet")
        local_reference = record.get("local_reference")
        if isinstance(local_reference, str):
            checked_references.append(_normalize_path_string(local_reference))
            errors.extend(_local_reference_errors(repo_root, local_reference))

    missing_ids = sorted(required_ids - present_ids)
    if missing_ids:
        errors.append(f"missing_required_evidence_ids:{','.join(missing_ids)}")
    extra_ids = sorted(present_ids - required_ids)
    if extra_ids:
        warnings.append(f"extra_evidence_ids_present:{','.join(extra_ids)}")

    return {
        "checked_local_references": sorted(set(checked_references)),
        "errors": sorted(errors),
        "linked_market_packet_id": source_evidence.get("linked_market_packet_id"),
        "missing_evidence_ids": missing_ids,
        "present_evidence_ids": sorted(present_ids),
        "status": "failed" if errors else "passed",
        "warnings": sorted(warnings),
    }


def _check_staleness_cases(case_set: Mapping[str, Any] | None) -> dict[str, Any]:
    if case_set is None:
        return {
            "case_results": [],
            "hard_blocker_case_ids": [],
            "status": "passed",
            "warnings": [],
        }

    errors = _missing_fields(case_set, ("case_records", "contract_version", "local_only", "rehearsal_id"), "staleness")
    if case_set.get("local_only") is not True:
        errors.append("staleness.local_only must be true")
    case_records = case_set.get("case_records")
    if not isinstance(case_records, list):
        errors.append("staleness.case_records must be a list")
        case_records = []

    case_results: list[dict[str, Any]] = []
    hard_blocker_ids: list[str] = []
    warnings: list[str] = []
    for index, record in enumerate(case_records):
        if not isinstance(record, Mapping):
            hard_blocker_ids.append(f"staleness.case_records[{index}]")
            continue
        field_errors = _missing_fields(record, REQUIRED_STALENESS_CASE_FIELDS, f"staleness.case_records[{index}]")
        if field_errors:
            hard_blocker_ids.append(str(record.get("case_id", f"staleness.case_records[{index}]")))
            warnings.extend(field_errors)
            continue
        case_id = str(record["case_id"])
        stale = _is_stale(record)
        severity = str(record.get("severity_if_stale", "hard_blocker"))
        status = "passed"
        if stale and severity == "warning":
            status = "warning"
            warnings.append(f"stale_case_warning:{case_id}")
        elif stale:
            status = "blocked"
            hard_blocker_ids.append(case_id)
        case_results.append(
            {
                "age_seconds": _age_seconds(record),
                "case_id": case_id,
                "evidence_id": record["evidence_id"],
                "maximum_age_seconds": record["maximum_age_seconds"],
                "severity": severity if stale else "none",
                "status": status,
            }
        )

    if hard_blocker_ids:
        status = "blocked"
    elif warnings or errors:
        status = "warning"
    else:
        status = "passed"
    return {
        "case_results": case_results,
        "hard_blocker_case_ids": sorted(set(hard_blocker_ids)),
        "status": status,
        "warnings": sorted(set([*errors, *warnings])),
    }


def _check_contradiction_cases(case_set: Mapping[str, Any] | None) -> dict[str, Any]:
    if case_set is None:
        return {
            "case_results": [],
            "detected_case_ids": [],
            "hard_blocker_case_ids": [],
            "status": "passed",
            "warnings": [],
        }

    errors = _missing_fields(case_set, ("case_records", "contract_version", "local_only", "rehearsal_id"), "contradiction")
    if case_set.get("local_only") is not True:
        errors.append("contradiction.local_only must be true")
    case_records = case_set.get("case_records")
    if not isinstance(case_records, list):
        errors.append("contradiction.case_records must be a list")
        case_records = []

    case_results: list[dict[str, Any]] = []
    detected_ids: list[str] = []
    hard_blocker_ids: list[str] = []
    warnings: list[str] = []
    for index, record in enumerate(case_records):
        if not isinstance(record, Mapping):
            hard_blocker_ids.append(f"contradiction.case_records[{index}]")
            continue
        field_errors = _missing_fields(record, REQUIRED_CONTRADICTION_CASE_FIELDS, f"contradiction.case_records[{index}]")
        if field_errors:
            hard_blocker_ids.append(str(record.get("case_id", f"contradiction.case_records[{index}]")))
            warnings.extend(field_errors)
            continue
        case_id = str(record["case_id"])
        detected = (
            record.get("values_match") is False
            or record.get("subject_keys_match") is False
            or record.get("left_field_present") is False
            or record.get("right_field_present") is False
        )
        severity = str(record.get("severity_if_detected", "hard_blocker"))
        status = "passed"
        if detected and severity == "warning":
            status = "warning"
            detected_ids.append(case_id)
            warnings.append(f"contradiction_case_warning:{case_id}")
        elif detected:
            status = "blocked"
            detected_ids.append(case_id)
            hard_blocker_ids.append(case_id)
        case_results.append(
            {
                "case_id": case_id,
                "detected": detected,
                "left_evidence_id": record["left_evidence_id"],
                "right_evidence_id": record["right_evidence_id"],
                "semantic_field": record["semantic_field"],
                "severity": severity if detected else "none",
                "status": status,
            }
        )

    if hard_blocker_ids:
        status = "blocked"
    elif warnings or errors:
        status = "warning"
    else:
        status = "passed"
    return {
        "case_results": case_results,
        "detected_case_ids": sorted(set(detected_ids)),
        "hard_blocker_case_ids": sorted(set(hard_blocker_ids)),
        "status": status,
        "warnings": sorted(set([*errors, *warnings])),
    }


def _apply_stop_condition_matrix(
    matrix: Mapping[str, Any] | None,
    status_context: Mapping[str, str],
) -> dict[str, Any]:
    if matrix is None:
        return {
            "hard_blocker_condition_ids": [],
            "status": "passed",
            "triggered_conditions": [],
            "warnings": [],
        }

    errors = _missing_fields(matrix, ("contract_version", "local_only", "rehearsal_id", "trigger_matrix_records"), "stop")
    if matrix.get("local_only") is not True:
        errors.append("stop.local_only must be true")
    records = matrix.get("trigger_matrix_records")
    if not isinstance(records, list):
        errors.append("stop.trigger_matrix_records must be a list")
        records = []

    triggered: list[dict[str, str]] = []
    hard_blocker_ids: list[str] = []
    warnings: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            hard_blocker_ids.append(f"stop.trigger_matrix_records[{index}]")
            continue
        field_errors = _missing_fields(record, REQUIRED_STOP_CONDITION_FIELDS, f"stop.trigger_matrix_records[{index}]")
        if field_errors:
            condition_id = str(record.get("condition_id", f"stop.trigger_matrix_records[{index}]"))
            hard_blocker_ids.append(condition_id)
            warnings.extend(field_errors)
            continue
        if record.get("enabled") is not True:
            continue
        condition_id = str(record["condition_id"])
        status_key = str(record["status_key"])
        trigger_statuses = set(str(item) for item in record["trigger_on_statuses"])
        observed_status = status_context.get(status_key, "not_available")
        force_trigger = record.get("force_trigger_for_rehearsal") is True
        if force_trigger or observed_status in trigger_statuses:
            triggered.append(
                {
                    "condition_id": condition_id,
                    "observed_status": observed_status,
                    "status_key": status_key,
                    "trigger_state_after_match": str(record["trigger_state_after_match"]),
                }
            )
            if record.get("severity") == "warning":
                warnings.append(f"stop_condition_warning:{condition_id}")
            else:
                hard_blocker_ids.append(condition_id)

    if hard_blocker_ids or errors:
        status = "blocked"
    elif warnings:
        status = "warning"
    else:
        status = "passed"
    return {
        "hard_blocker_condition_ids": sorted(set([*hard_blocker_ids, *errors])),
        "status": status,
        "triggered_conditions": triggered,
        "warnings": sorted(set(warnings)),
    }


def _repo_root(repo_root: str | Path | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    return Path(__file__).resolve().parents[2]


def _resolve_input_path(path: str | Path | None) -> Path:
    if path is None:
        raise StaticReplayRehearsalError("input path is required")
    normalized = _normalize_path_string(path)
    if _is_network_like(normalized):
        raise StaticReplayRehearsalError(f"input path must be local: {normalized}")
    _reject_sensitive_path(Path(path))
    resolved = Path(path)
    if not resolved.exists():
        raise StaticReplayRehearsalError(f"missing input path: {normalized}")
    return resolved


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise StaticReplayRehearsalError(f"JSON payload must be an object: {_normalize_path_string(path)}")
    return payload


def _local_reference_errors(repo_root: Path, local_reference: str) -> list[str]:
    normalized = _normalize_path_string(local_reference)
    errors: list[str] = []
    if _is_network_like(normalized):
        return [f"network_reference_not_allowed:{normalized}"]
    if normalized.startswith("/") or normalized.startswith("\\"):
        return [f"absolute_reference_not_allowed:{normalized}"]
    if any(part in {"", ".."} for part in normalized.split("/")):
        return [f"unsafe_reference_not_allowed:{normalized}"]
    if normalized.startswith(FORBIDDEN_REFERENCE_PREFIXES):
        return [f"forbidden_reference_not_allowed:{normalized}"]
    if not normalized.startswith(ALLOWED_LOCAL_REFERENCE_PREFIXES):
        return [f"unapproved_reference_prefix:{normalized}"]
    resolved = (repo_root / Path(*normalized.split("/"))).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError:
        errors.append(f"reference_outside_repo:{normalized}")
    if not resolved.exists():
        errors.append(f"missing_local_reference:{normalized}")
    return errors


def _safety_boundary_errors(boundaries: Any, path: str) -> list[str]:
    if not isinstance(boundaries, Mapping):
        return [f"{path} must be an object"]
    errors = [f"{path}.{key} must be true" for key in TRUE_SAFETY_BOUNDARIES if boundaries.get(key) is not True]
    errors.extend(
        f"{path}.{key} must be false"
        for key, value in boundaries.items()
        if key.endswith("_allowed") and value is not False
    )
    return sorted(errors)


def _missing_fields(payload: Mapping[str, Any], required_fields: Sequence[str], label: str) -> list[str]:
    return [f"{label}.{field} is required" for field in required_fields if field not in payload]


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _is_stale(record: Mapping[str, Any]) -> bool:
    if record.get("timestamp_required") is not True:
        return False
    if record.get("timestamp_field_present") is not True:
        return True
    return _age_seconds(record) > int(record["maximum_age_seconds"])


def _age_seconds(record: Mapping[str, Any]) -> int:
    if record.get("timestamp_field_present") is not True:
        return 0
    observed = _parse_utc(str(record["observed_timestamp_utc"]))
    reference = _parse_utc(str(record["reference_timestamp_utc"]))
    return int((reference - observed).total_seconds())


def _parse_utc(value: str) -> datetime:
    if not value.endswith("Z"):
        raise StaticReplayRehearsalError(f"timestamp must be UTC Z format: {value}")
    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00").astimezone(timezone.utc)


def _is_network_like(value: str) -> bool:
    lowered = value.lower()
    return "://" in lowered or lowered.startswith("http:") or lowered.startswith("https:")


def _has_forbidden_action_text(value: str) -> bool:
    tokens = _normalized_tokens(value)
    return bool(tokens & FORBIDDEN_ACTION_TEXT_TOKENS)


def _has_sensitive_text_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in SENSITIVE_TEXT_MARKERS)


def _contains_forbidden_action_text(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_forbidden_action_text(nested) for nested in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden_action_text(item) for item in value)
    return isinstance(value, str) and _has_forbidden_action_text(value)


def _contains_sensitive_text_marker(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_sensitive_text_marker(nested) for nested in value.values())
    if isinstance(value, list):
        return any(_contains_sensitive_text_marker(item) for item in value)
    return isinstance(value, str) and _has_sensitive_text_marker(value)


def _normalized_tokens(value: str) -> set[str]:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    return {token for token in normalized.split("_") if token}


def _reject_sensitive_path(path: Path) -> None:
    lowered_parts = {part.lower() for part in path.parts}
    if lowered_parts & SENSITIVE_PATH_PARTS:
        raise StaticReplayRehearsalError(f"sensitive input path is not allowed: {_normalize_path_string(path)}")


def _normalize_optional_path(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return _normalize_path_string(path)


def _normalize_path_string(path: str | Path) -> str:
    return str(path).replace("\\", "/")


if __name__ == "__main__":
    raise SystemExit(main())
