from __future__ import annotations

import argparse
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text
from pm_bot.practical.public_read_only_fetch_contract import assert_valid_fetch_plan
from pm_bot.practical.public_source_registry import blocked_source_categories

OPERATOR_APPROVAL_CONTRACT_VERSION = "pmbot_public_read_only_fetch_operator_approval.v1"


class PublicFetchOperatorApprovalError(ValueError):
    pass


def build_pending_operator_approval(fetch_plan: Mapping[str, Any]) -> dict[str, Any]:
    assert_valid_fetch_plan(fetch_plan)
    requested_categories = sorted(
        {
            clean_text(source.get("source_category"))
            for source in fetch_plan.get("requested_sources", [])
            if isinstance(source, Mapping) and clean_text(source.get("source_category"))
        }
    )
    approval = {
        "contract_version": OPERATOR_APPROVAL_CONTRACT_VERSION,
        "approval_id": f"{fetch_plan['fetch_plan_id']}.operator_approval.pending",
        "fetch_plan_id": fetch_plan["fetch_plan_id"],
        "operator_approval_required": True,
        "operator_approval_granted": False,
        "approved_by": None,
        "approved_at": None,
        "allowed_scope": {
            "market_ids": list(fetch_plan["market_ids"]),
            "source_categories": requested_categories,
            "request_count": len(fetch_plan.get("requested_sources", [])),
            "capture_mode": "future_public_read_only_fetch_after_separate_approval",
        },
        "blocked_scope": [
            "authenticated endpoints",
            "credentials or private API keys",
            "wallet, private key, signing, custody, or KYC paths",
            "orders, trading endpoints, or real-money actions",
            "scheduler, daemon, watcher, polling, or unattended automation",
            "live recommendations or quantitative market signals used for execution",
        ],
        "max_request_count": fetch_plan["max_request_count"],
        "max_markets": len(fetch_plan["market_ids"]),
        "allowed_source_categories": requested_categories,
        "blocked_source_categories": blocked_source_categories(),
        "safety_acknowledgements": [
            "Approval is pending.",
            "This record does not grant permission to fetch.",
            "Any future fetch must save evidence before replay.",
            "Any future analysis update must replay saved evidence first.",
        ],
        "live_fetch_enabled_after_approval": False,
        "created_at": GENERATED_AT,
        "safety_summary": safe_summary(),
    }
    validation = validate_operator_approval(approval)
    if not validation["valid"]:
        raise PublicFetchOperatorApprovalError("; ".join(validation["errors"]))
    return approval


def validate_operator_approval(record: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    required = (
        "contract_version",
        "approval_id",
        "fetch_plan_id",
        "operator_approval_required",
        "operator_approval_granted",
        "approved_by",
        "approved_at",
        "allowed_scope",
        "blocked_scope",
        "max_request_count",
        "max_markets",
        "allowed_source_categories",
        "blocked_source_categories",
        "safety_acknowledgements",
        "live_fetch_enabled_after_approval",
    )
    missing = [field for field in required if field not in record]
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
        return {"valid": False, "errors": errors}
    if record.get("contract_version") != OPERATOR_APPROVAL_CONTRACT_VERSION:
        errors.append("contract_version must be " + OPERATOR_APPROVAL_CONTRACT_VERSION)
    if record.get("operator_approval_required") is not True:
        errors.append("operator_approval_required must be true")
    if record.get("operator_approval_granted") is not False:
        errors.append("operator_approval_granted must remain false in the pending sample")
    if record.get("approved_by") is not None:
        errors.append("approved_by must be null while pending")
    if record.get("approved_at") is not None:
        errors.append("approved_at must be null while pending")
    if record.get("live_fetch_enabled_after_approval") is not False:
        errors.append("live_fetch_enabled_after_approval must be false in this task")
    if not isinstance(record.get("allowed_scope"), Mapping):
        errors.append("allowed_scope must be an object")
    if not isinstance(record.get("blocked_scope"), list) or not record["blocked_scope"]:
        errors.append("blocked_scope must be a non-empty list")
    if not isinstance(record.get("allowed_source_categories"), list):
        errors.append("allowed_source_categories must be a list")
    if not isinstance(record.get("blocked_source_categories"), list) or not record["blocked_source_categories"]:
        errors.append("blocked_source_categories must be a non-empty list")
    if not isinstance(record.get("max_request_count"), int) or record["max_request_count"] < 1:
        errors.append("max_request_count must be a positive integer")
    if not isinstance(record.get("max_markets"), int) or record["max_markets"] < 1:
        errors.append("max_markets must be a positive integer")
    return {"valid": not errors, "errors": errors}


def render_operator_approval_markdown(record: Mapping[str, Any]) -> str:
    validation = validate_operator_approval(record)
    lines = [
        "# PMBOT Public Fetch Operator Approval",
        "",
        f"- Approval ID: `{record.get('approval_id')}`",
        f"- Fetch plan ID: `{record.get('fetch_plan_id')}`",
        f"- Approval required: `{str(record.get('operator_approval_required')).lower()}`",
        f"- Approval granted: `{str(record.get('operator_approval_granted')).lower()}`",
        f"- Live fetch enabled after approval: `{str(record.get('live_fetch_enabled_after_approval')).lower()}`",
        "",
        "## Allowed Scope",
        "",
        *bullet_lines(f"`{category}`" for category in record.get("allowed_source_categories", [])),
        "",
        "## Blocked Scope",
        "",
        *bullet_lines(record.get("blocked_scope", [])),
        "",
        "## Acknowledgements",
        "",
        *bullet_lines(record.get("safety_acknowledgements", [])),
        "",
        "## Validation",
        "",
        *bullet_lines(validation["errors"]),
    ]
    return "\n".join(lines) + "\n"


def write_operator_approval(
    record: Mapping[str, Any],
    *,
    out_json_path: str | None = None,
    out_md_path: str | None = None,
) -> dict[str, Any]:
    record_dict = dict(record)
    validation = validate_operator_approval(record_dict)
    if not validation["valid"]:
        raise PublicFetchOperatorApprovalError("; ".join(validation["errors"]))
    if out_json_path is not None:
        write_json(out_json_path, record_dict)
    if out_md_path is not None:
        write_text(out_md_path, render_operator_approval_markdown(record_dict))
    return record_dict


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a pending public read-only fetch approval record.")
    parser.add_argument("--fetch-plan", required=True, help="Input fetch plan JSON.")
    parser.add_argument("--out-json", required=True, help="Output approval JSON.")
    parser.add_argument("--out-md", required=True, help="Output approval Markdown.")
    args = parser.parse_args(argv)
    fetch_plan = load_json_object(args.fetch_plan, label="fetch plan")
    approval = build_pending_operator_approval(fetch_plan)
    write_operator_approval(approval, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
