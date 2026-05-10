from __future__ import annotations

import argparse
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_string_list, clean_text, load_json_object, safe_summary, write_json, write_text
from pm_bot.practical.public_source_registry import (
    allowed_source_categories,
    blocked_source_categories,
    validate_requested_source,
)

FETCH_PLAN_CONTRACT_VERSION = "pmbot_public_read_only_fetch_plan.v1"

REQUIRED_FETCH_PLAN_FIELDS = (
    "contract_version",
    "fetch_plan_id",
    "created_at",
    "market_ids",
    "requested_sources",
    "allowed_public_sources",
    "blocked_sources",
    "auth_required",
    "credentials_required",
    "wallet_required",
    "trading_endpoint_allowed",
    "order_endpoint_allowed",
    "max_request_count",
    "timeout_seconds",
    "retry_policy",
    "evidence_save_required",
    "replay_required_before_analysis_update",
    "operator_approval_required",
    "operator_approval_granted",
    "live_fetch_performed",
    "safety_notes",
)


class PublicReadOnlyFetchContractError(ValueError):
    pass


def build_public_read_only_fetch_plan(
    *,
    fetch_plan_id: str,
    market_ids: Sequence[str],
    requested_sources: Sequence[Mapping[str, Any]],
    max_request_count: int,
    timeout_seconds: int = 10,
    retry_policy: Mapping[str, Any] | None = None,
    safety_notes: Sequence[str] = (),
) -> dict[str, Any]:
    plan = {
        "contract_version": FETCH_PLAN_CONTRACT_VERSION,
        "fetch_plan_id": clean_text(fetch_plan_id),
        "created_at": GENERATED_AT,
        "market_ids": [clean_text(market_id) for market_id in market_ids],
        "requested_sources": [dict(source) for source in requested_sources],
        "allowed_public_sources": allowed_source_categories(),
        "blocked_sources": blocked_source_categories(),
        "auth_required": False,
        "credentials_required": False,
        "wallet_required": False,
        "trading_endpoint_allowed": False,
        "order_endpoint_allowed": False,
        "max_request_count": int(max_request_count),
        "timeout_seconds": int(timeout_seconds),
        "retry_policy": dict(
            retry_policy
            or {
                "retry_enabled": False,
                "max_attempts": 0,
                "backoff_seconds": 0,
            }
        ),
        "evidence_save_required": True,
        "replay_required_before_analysis_update": True,
        "operator_approval_required": True,
        "operator_approval_granted": False,
        "live_fetch_performed": False,
        "safety_notes": list(safety_notes)
        or [
            "Local fetch plan only.",
            "No live fetch is performed by this plan.",
            "Operator approval remains required before any future public read-only request.",
        ],
        "safety_summary": safe_summary(),
    }
    validation = validate_fetch_plan(plan)
    if not validation["valid"]:
        raise PublicReadOnlyFetchContractError("; ".join(validation["errors"]))
    return plan


def validate_fetch_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = [field for field in REQUIRED_FETCH_PLAN_FIELDS if field not in plan]
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
        return {"valid": False, "errors": errors, "warnings": warnings}

    if plan.get("contract_version") != FETCH_PLAN_CONTRACT_VERSION:
        errors.append("contract_version must be " + FETCH_PLAN_CONTRACT_VERSION)
    if not clean_text(plan.get("fetch_plan_id")):
        errors.append("fetch_plan_id is required")
    if not isinstance(plan.get("market_ids"), list) or not plan["market_ids"]:
        errors.append("market_ids must be a non-empty list")
    if not isinstance(plan.get("requested_sources"), list) or not plan["requested_sources"]:
        errors.append("requested_sources must be a non-empty list")
    if plan.get("auth_required") is not False:
        errors.append("auth_required must be false")
    if plan.get("credentials_required") is not False:
        errors.append("credentials_required must be false")
    if plan.get("wallet_required") is not False:
        errors.append("wallet_required must be false")
    if plan.get("trading_endpoint_allowed") is not False:
        errors.append("trading_endpoint_allowed must be false")
    if plan.get("order_endpoint_allowed") is not False:
        errors.append("order_endpoint_allowed must be false")
    if plan.get("evidence_save_required") is not True:
        errors.append("evidence_save_required must be true")
    if plan.get("replay_required_before_analysis_update") is not True:
        errors.append("replay_required_before_analysis_update must be true")
    if plan.get("operator_approval_required") is not True:
        errors.append("operator_approval_required must be true")
    if plan.get("operator_approval_granted") is not False:
        errors.append("operator_approval_granted must be false for this preparation contract")
    if plan.get("live_fetch_performed") is not False:
        errors.append("live_fetch_performed must be false")
    if not isinstance(plan.get("max_request_count"), int) or plan["max_request_count"] < 1:
        errors.append("max_request_count must be a positive integer")
    if not isinstance(plan.get("timeout_seconds"), int) or plan["timeout_seconds"] < 1:
        errors.append("timeout_seconds must be a positive integer")
    if not isinstance(plan.get("retry_policy"), Mapping):
        errors.append("retry_policy must be an object")
    if not isinstance(plan.get("safety_notes"), list):
        errors.append("safety_notes must be a list")

    requested_sources = plan.get("requested_sources", [])
    if isinstance(requested_sources, list) and isinstance(plan.get("max_request_count"), int):
        if len(requested_sources) > plan["max_request_count"]:
            errors.append("requested source count exceeds max_request_count")
    market_ids = {clean_text(market_id) for market_id in plan.get("market_ids", []) if clean_text(market_id)}
    for index, source in enumerate(requested_sources if isinstance(requested_sources, list) else []):
        if not isinstance(source, Mapping):
            errors.append(f"requested_sources[{index}] must be an object")
            continue
        source_market_id = clean_text(source.get("market_id"))
        if source_market_id and source_market_id not in market_ids:
            errors.append(f"requested_sources[{index}] market_id is not in market_ids")
        category_validation = validate_requested_source(source)
        if category_validation["blocked"]:
            errors.append(
                f"requested_sources[{index}] category is blocked: {category_validation['source_category']}"
            )
        if source.get("auth_required") is True:
            errors.append(f"requested_sources[{index}] auth_required must not be true")
        if source.get("credentials_required") is True:
            errors.append(f"requested_sources[{index}] credentials_required must not be true")
        if source.get("wallet_required") is True:
            errors.append(f"requested_sources[{index}] wallet_required must not be true")
        if source.get("trading_endpoint") is True or source.get("order_endpoint") is True:
            errors.append(f"requested_sources[{index}] trading/order endpoint flags must not be true")
        if not clean_text(source.get("expected_evidence_type")):
            warnings.append(f"requested_sources[{index}] expected_evidence_type is empty")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def assert_valid_fetch_plan(plan: Mapping[str, Any]) -> None:
    validation = validate_fetch_plan(plan)
    if not validation["valid"]:
        raise PublicReadOnlyFetchContractError("; ".join(validation["errors"]))


def render_fetch_plan_markdown(plan: Mapping[str, Any]) -> str:
    validation = validate_fetch_plan(plan)
    lines = [
        "# PMBOT Public Read-Only Fetch Plan",
        "",
        f"- Contract: `{plan.get('contract_version')}`",
        f"- Fetch plan ID: `{plan.get('fetch_plan_id')}`",
        f"- Created at: `{plan.get('created_at')}`",
        f"- Markets: {len(plan.get('market_ids', []))}",
        f"- Planned request count: {len(plan.get('requested_sources', []))}",
        f"- Max request count: {plan.get('max_request_count')}",
        f"- Operator approval required: `{str(plan.get('operator_approval_required')).lower()}`",
        f"- Operator approval granted: `{str(plan.get('operator_approval_granted')).lower()}`",
        f"- Live fetch performed: `{str(plan.get('live_fetch_performed')).lower()}`",
        f"- Validation valid: `{str(validation['valid']).lower()}`",
        "",
        "## Requested Sources",
        "",
    ]
    for source in plan.get("requested_sources", []):
        lines.extend(
            [
                f"- `{source.get('planned_source_id') or source.get('source_id')}` `{source.get('source_category')}`",
                f"  Market: `{source.get('market_id')}` {source.get('market_title', '')}",
                f"  Evidence: {source.get('expected_evidence_type', '')}",
                f"  Role: {source.get('expected_evidence_role', '')}",
                f"  Approval required: `{str(source.get('operator_approval_required', True)).lower()}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Allowed Categories",
            "",
            *bullet_lines(f"`{category}`" for category in plan.get("allowed_public_sources", [])),
            "",
            "## Blocked Categories",
            "",
            *bullet_lines(f"`{category}`" for category in plan.get("blocked_sources", [])),
            "",
            "## Safety Notes",
            "",
            *bullet_lines(clean_string_list(plan.get("safety_notes"))),
            "",
            "## Validation",
            "",
            *bullet_lines(validation["errors"]),
        ]
    )
    return "\n".join(lines) + "\n"


def write_fetch_plan(
    plan: Mapping[str, Any],
    *,
    out_json_path: str | None = None,
    out_md_path: str | None = None,
) -> dict[str, Any]:
    plan_dict = dict(plan)
    assert_valid_fetch_plan(plan_dict)
    if out_json_path is not None:
        write_json(out_json_path, plan_dict)
    if out_md_path is not None:
        write_text(out_md_path, render_fetch_plan_markdown(plan_dict))
    return plan_dict


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and render a local-only public read-only fetch plan.")
    parser.add_argument("--fetch-plan", required=True, help="Input fetch plan JSON.")
    parser.add_argument("--out-json", required=True, help="Output validated fetch plan JSON.")
    parser.add_argument("--out-md", required=True, help="Output fetch plan Markdown.")
    args = parser.parse_args(argv)
    plan = load_json_object(args.fetch_plan, label="fetch plan")
    write_fetch_plan(plan, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
