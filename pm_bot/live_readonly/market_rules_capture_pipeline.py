import argparse
import json
from pathlib import Path


TASK_ID = "PMBOT-SOURCE-008-READONLY-MARKET-RULES-CAPTURE-PIPELINE-PROTOCOL"
ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = "pm_bot/live_readonly/market_rules_capture_protocol.v1.json"
DEFAULT_OUTPUT_DIR = "pm_bot/live_readonly"

CURRENT_MARKET_IDS = (
    "563650",
    "569332",
    "569333",
    "569334",
    "569343",
    "569344",
    "569366",
    "569368",
    "569373",
    "573656",
    "597964",
    "598936",
    "691547",
    "692258",
)


def _zero_safety_summary():
    return {
        "network_allowed_explicitly": False,
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "external_network_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "market_action_guidance_generated": False,
        "operator_review_only": True,
        "analysis_only": True,
        "no_trading_authority": True,
        "no_runtime_authority": True,
        "no_queue_authority": True,
        "no_wallet_or_order_authority": True,
        "no_market_action_guidance": True,
    }


def _resolve(path, root=ROOT):
    value = Path(path)
    return value if value.is_absolute() else Path(root) / value


def _load_protocol(root=ROOT):
    with _resolve(PROTOCOL_PATH, root=root).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_protocol_only_status(root=ROOT):
    protocol = _load_protocol(root=root)
    return {
        "schema_version": "market_rules_capture_protocol_status.v1",
        "task_id": TASK_ID,
        "status": "protocol_only_no_network",
        "protocol_path": PROTOCOL_PATH,
        "current_stage": "STAGE_0_PROTOCOL_ONLY",
        "current_market_count": len(CURRENT_MARKET_IDS),
        "current_market_ids": list(CURRENT_MARKET_IDS),
        "implemented_cli_modes": [
            "protocol-only status",
            "dry-run plan only",
        ],
        "future_pipeline_stages_defined": [
            stage["stage_id"] for stage in protocol["future_pipeline_stages"]
        ],
        "write_scope": "protocol_status_or_dry_run_plan_artifacts_only",
        "network_imports_present": False,
        "fetch_performed": False,
        "safety_summary": _zero_safety_summary(),
        **_zero_safety_summary(),
    }


def _market_plan(market_id):
    return {
        "market_id": market_id,
        "status": "planned_not_fetched",
        "intended_future_raw_artifact_path": (
            "pm_bot/live_readonly/market_rules_raw_fetch/"
            f"{market_id}_market_rules_raw_fetch.v1.json"
        ),
        "intended_future_normalized_candidate_path": (
            "pm_bot/live_readonly/market_rules_normalized_candidates/"
            f"{market_id}_market_rules_normalized_candidate.v1.json"
        ),
        "intended_future_capture_template_path": (
            "pm_bot/llm/manual_resolution_source_capture/"
            f"{market_id}_resolution_source_capture.v1.json"
        ),
        "planned_status_after_fill": "draft",
        "fields_to_fill": [
            "full_market_resolution_criteria_text",
            "full_resolution_rules",
            "official_source_references",
            "official_source_urls_or_rule_references",
            "source_timestamps",
            "source_reliability_review",
            "reviewed_local_evidence_references",
            "non_placeholder_evidence_notes",
        ],
        "fields_to_preserve": [
            "market_id",
            "market_title_or_question",
            "category",
            "current_openrouter_review_status",
            "current_readiness_band",
        ],
        "will_auto_promote_to_ready": False,
        "canonical_packets_mutated": False,
        "operator_review_required": True,
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "no_trading_authority": True,
        "no_market_action_guidance": True,
    }


def validate_dry_run_plan(plan):
    errors = []
    for market_plan in plan["market_plans"]:
        if market_plan["status"] != "planned_not_fetched":
            errors.append(f"{market_plan['market_id']}: unexpected status")
        if market_plan["network_calls_performed"] != 0:
            errors.append(f"{market_plan['market_id']}: network calls were recorded")
        if market_plan["polymarket_api_calls_performed"] != 0:
            errors.append(f"{market_plan['market_id']}: Polymarket calls were recorded")
        if market_plan["planned_status_after_fill"] != "draft":
            errors.append(f"{market_plan['market_id']}: auto-fill status is not draft")
        if market_plan["will_auto_promote_to_ready"] is not False:
            errors.append(f"{market_plan['market_id']}: ready auto-promotion requested")
        if market_plan["canonical_packets_mutated"] is not False:
            errors.append(f"{market_plan['market_id']}: canonical mutation requested")
        if market_plan["operator_review_required"] is not True:
            errors.append(f"{market_plan['market_id']}: operator review not required")
        if market_plan["no_trading_authority"] is not True:
            errors.append(f"{market_plan['market_id']}: trading authority present")
        if market_plan["no_market_action_guidance"] is not True:
            errors.append(f"{market_plan['market_id']}: market action guidance present")

    safety = plan["safety_summary"]
    expected_zero_false = {
        "network_allowed_explicitly": False,
        "polymarket_api_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "external_network_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "market_action_guidance_generated": False,
    }
    for field, expected in expected_zero_false.items():
        if safety.get(field) != expected:
            errors.append(f"safety_summary.{field} expected {expected!r}")

    return {
        "validator_status": "passed" if not errors else "failed",
        "errors": errors,
        "draft_only_auto_fill": not errors,
        "no_ready_auto_promotion": not errors,
        "canonical_packets_mutated": False,
        "network_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "operator_review_required": True,
    }


def build_dry_run_plan(market_ids):
    market_ids = list(market_ids)
    plan = {
        "schema_version": "market_rules_capture_dry_run_plan.v1",
        "task_id": TASK_ID,
        "status": "dry_run_planned_not_fetched",
        "mode": "dry_run",
        "target_market_count": len(market_ids),
        "target_market_ids": market_ids,
        "market_plans": [_market_plan(market_id) for market_id in market_ids],
        "future_pipeline_not_executed": True,
        "fetch_performed": False,
        "write_scope": "dry_run_plan_artifacts_only",
        "safety_summary": _zero_safety_summary(),
        **_zero_safety_summary(),
    }
    plan["validation"] = validate_dry_run_plan(plan)
    return plan


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _render_protocol_status_md(status):
    return "\n".join(
        [
            "# PMBOT SOURCE-008 Market Rules Capture Protocol Status",
            "",
            f"- task_id: {status['task_id']}",
            f"- status: {status['status']}",
            f"- current_stage: {status['current_stage']}",
            f"- current_market_count: {status['current_market_count']}",
            "- network_allowed_explicitly: false",
            "- network_calls_performed: 0",
            "- polymarket_api_calls_performed: 0",
            "- openrouter_calls_performed: 0",
            "",
            "## Safety Boundary",
            "",
            "- no network calls",
            "- no Polymarket API calls",
            "- no OpenRouter calls",
            "- no authenticated endpoints",
            "- no wallet or private key access",
            "- no orders",
            "- no trading runtime changes",
            "- no dispatcher changes",
            "- no background workers",
            "- no queue mutation",
            "- no browser automation",
            "- no canonical packet mutation",
            "- no buy, sell, hold, enter, exit, probability, EV, edge, confidence, or side selection text",
            "",
        ]
    )


def _render_dry_run_plan_md(plan):
    lines = [
        "# PMBOT SOURCE-008 Market Rules Capture Dry-Run Plan",
        "",
        f"- task_id: {plan['task_id']}",
        f"- status: {plan['status']}",
        f"- target_market_count: {plan['target_market_count']}",
        "- network_calls_performed: 0",
        "- polymarket_api_calls_performed: 0",
        "- validator_status: " + plan["validation"]["validator_status"],
        "",
        "## Planned Markets",
        "",
    ]
    for market_plan in plan["market_plans"]:
        lines.extend(
            [
                f"- {market_plan['market_id']}: {market_plan['status']}",
                f"  - future raw artifact: {market_plan['intended_future_raw_artifact_path']}",
                (
                    "  - future normalized candidate: "
                    + market_plan["intended_future_normalized_candidate_path"]
                ),
                (
                    "  - future capture template: "
                    + market_plan["intended_future_capture_template_path"]
                ),
                "  - planned_status_after_fill: draft",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- no network calls",
            "- no data fetching",
            "- no capture template mutation in this dry run",
            "- no ready_for_local_review or reviewed auto-promotion",
            "- no canonical packet mutation",
            "- no wallet, order, runtime, dispatcher, background worker, queue, or browser authority",
            "- no buy, sell, hold, enter, exit, probability, EV, edge, confidence, or side selection text",
            "",
        ]
    )
    return "\n".join(lines)


def _write_protocol_status(output_dir, status):
    output_root = _resolve(output_dir)
    _write_json(output_root / "market_rules_capture_protocol_status.v1.json", status)
    (output_root / "market_rules_capture_protocol_status.v1.md").write_text(
        _render_protocol_status_md(status),
        encoding="utf-8",
    )


def _write_dry_run_plan(output_dir, plan):
    output_root = _resolve(output_dir)
    _write_json(output_root / "market_rules_capture_dry_run_plan.v1.json", plan)
    (output_root / "market_rules_capture_dry_run_plan.v1.md").write_text(
        _render_dry_run_plan_md(plan),
        encoding="utf-8",
    )


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Build SOURCE-008 protocol-only or dry-run market rules capture plans."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--protocol-only",
        action="store_true",
        help="Print local protocol status without network behavior.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Print a no-fetch future capture plan without network behavior.",
    )
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--market-id", help="Current market id to include in a dry-run plan.")
    target.add_argument(
        "--all-current-markets",
        action="store_true",
        help="Include the current fixed 14-market SOURCE capture set.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write protocol status or dry-run plan artifacts only.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for --write artifacts.",
    )
    args = parser.parse_args(argv)

    if args.protocol_only and (args.market_id or args.all_current_markets):
        parser.error("--protocol-only does not accept market selection arguments")
    if args.dry_run and not (args.market_id or args.all_current_markets):
        parser.error("--dry-run requires --market-id or --all-current-markets")
    if args.market_id and args.market_id not in CURRENT_MARKET_IDS:
        parser.error("--market-id must be one of the current SOURCE capture market ids")
    return args


def main(argv):
    args = _parse_args(argv)
    if args.protocol_only:
        status = build_protocol_only_status(ROOT)
        if args.write:
            _write_protocol_status(args.output_dir, status)
        print(json.dumps(status, indent=2, ensure_ascii=True))
        return 0

    market_ids = CURRENT_MARKET_IDS if args.all_current_markets else (args.market_id,)
    plan = build_dry_run_plan(market_ids)
    if args.write:
        _write_dry_run_plan(args.output_dir, plan)
    print(json.dumps(plan, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
