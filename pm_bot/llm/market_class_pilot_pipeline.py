import argparse
import json
from pathlib import Path


TASK_ID = "PMBOT-SOURCE-008B-MARKET-CLASS-PILOT-PROTOCOL-ESPORTS-WEATHER-CRYPTO"
ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = "pm_bot/llm"
CLASS_ORDER = ("esports", "weather", "crypto")

TAXONOMY_PATH = "pm_bot/llm/market_class_pilot_taxonomy.v1.json"
SELECTION_CRITERIA_PATH = "pm_bot/llm/market_class_pilot_selection_criteria.v1.json"
STATUS_JSON = "market_class_pilot_protocol_status.v1.json"
STATUS_MD = "market_class_pilot_protocol_status.v1.md"
DRY_RUN_JSON = "market_class_pilot_dry_run_plan.v1.json"
DRY_RUN_MD = "market_class_pilot_dry_run_plan.v1.md"


def _resolve(path, root=ROOT):
    value = Path(path)
    return value if value.is_absolute() else Path(root) / value


def _load_json(path, root=ROOT):
    with _resolve(path, root=root).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _base_safety_summary():
    return {
        "protocol_only": True,
        "local_only": True,
        "network_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "runtime_wiring_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "market_action_guidance_generated": False,
        "operator_review_only": True,
    }


def _current_state(root=ROOT):
    ingest_result = _load_json(
        "pm_bot/llm/manual_resolution_source_capture_ingest_result.v1.json",
        root=root,
    )
    gate = _load_json("pm_bot/llm/post_capture_batch_readiness_gate.v1.json", root=root)
    return {
        "real_ingested_template_count": ingest_result["real_ingested_template_count"],
        "draft_ingested_template_count": gate["draft_ingested_template_count"],
        "ready_ingested_template_count": gate["ready_ingested_template_count"],
        "future_live_002_allowed": gate["future_live_002_allowed"],
        "readiness": gate["live_readonly_api_discovery_readiness"],
    }


def build_protocol_status(root=ROOT):
    taxonomy = _load_json(TAXONOMY_PATH, root=root)
    criteria = _load_json(SELECTION_CRITERIA_PATH, root=root)
    state = _current_state(root=root)
    return {
        "schema_version": "market_class_pilot_protocol_status.v1",
        "task_id": TASK_ID,
        "status": "protocol_only_no_network",
        "implemented_now": [
            "taxonomy",
            "selection criteria",
            "candidate contracts",
            "operator review contract",
            "placeholder CLI",
            "protocol status artifact",
            "dry-run plan artifact",
        ],
        "class_order": list(CLASS_ORDER),
        "taxonomy_path": TAXONOMY_PATH,
        "selection_criteria_path": SELECTION_CRITERIA_PATH,
        "selection_order": criteria["selection_order"],
        "taxonomy_classes": list(taxonomy["classes"].keys()),
        "current_source_state": state,
        "future_testing_order": list(CLASS_ORDER),
        "write_scope": "protocol_status_or_dry_run_plan_artifacts_only",
        "fetch_performed": False,
        "runtime_wiring_changed": False,
        "canonical_packets_mutated": False,
        "safety_summary": _base_safety_summary(),
    }


def _class_plan(market_class, taxonomy):
    class_spec = taxonomy["classes"][market_class]
    return {
        "market_class": market_class,
        "status": "planned_not_fetched",
        "candidate_count": 0,
        "future_candidate_contract": (
            "pm_bot/llm/market_class_pilot_candidate_contract.v1.json"
        ),
        "future_source_capture_candidate_contract": (
            "pm_bot/llm/market_class_source_capture_candidate_contract.v1.json"
        ),
        "future_operator_review_contract": (
            "pm_bot/llm/market_class_operator_review_contract.v1.json"
        ),
        "selection_checks": [
            "clear_resolution_wording",
            "identifiable_official_source",
            "near_or_mid_term_market",
            "avoid_ambiguous_or_sensitive_markets",
        ],
        "required_capture_fields": class_spec["required_capture_fields"],
        "operator_review_focus": class_spec["operator_review_focus"],
        "future_read_only_fetch_requirements": class_spec[
            "future_read_only_fetch_requirements"
        ],
        "network_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "canonical_packets_mutated": False,
        "operator_review_required": True,
        "market_action_guidance_generated": False,
    }


def build_dry_run_plan(market_classes=None, root=ROOT):
    taxonomy = _load_json(TAXONOMY_PATH, root=root)
    selected = list(market_classes or CLASS_ORDER)
    plan = {
        "schema_version": "market_class_pilot_dry_run_plan.v1",
        "task_id": TASK_ID,
        "status": "dry_run_planned_not_fetched",
        "mode": "dry_run",
        "class_order": list(CLASS_ORDER),
        "target_classes": selected,
        "target_class_count": len(selected),
        "class_plans": [_class_plan(item, taxonomy) for item in selected],
        "future_pipeline_not_executed": True,
        "fetch_performed": False,
        "write_scope": "dry_run_plan_artifacts_only",
        "current_source_state": _current_state(root=root),
        "safety_summary": _base_safety_summary(),
    }
    plan["validation"] = validate_dry_run_plan(plan)
    return plan


def validate_dry_run_plan(plan):
    errors = []
    for class_plan in plan["class_plans"]:
        if class_plan["status"] != "planned_not_fetched":
            errors.append(f"{class_plan['market_class']}: unexpected status")
        if class_plan["candidate_count"] != 0:
            errors.append(f"{class_plan['market_class']}: candidates were created")
        if class_plan["network_calls_performed"] != 0:
            errors.append(f"{class_plan['market_class']}: network calls were recorded")
        if class_plan["polymarket_api_calls_performed"] != 0:
            errors.append(f"{class_plan['market_class']}: Polymarket calls were recorded")
        if class_plan["openrouter_calls_performed"] != 0:
            errors.append(f"{class_plan['market_class']}: OpenRouter calls were recorded")
        if class_plan["canonical_packets_mutated"] is not False:
            errors.append(f"{class_plan['market_class']}: canonical mutation requested")
        if class_plan["operator_review_required"] is not True:
            errors.append(f"{class_plan['market_class']}: operator review not required")
        if class_plan["market_action_guidance_generated"] is not False:
            errors.append(f"{class_plan['market_class']}: market action guidance present")

    safety = plan["safety_summary"]
    expected = _base_safety_summary()
    for field, value in expected.items():
        if safety.get(field) != value:
            errors.append(f"safety_summary.{field} expected {value!r}")

    return {
        "validator_status": "passed" if not errors else "failed",
        "errors": errors,
        "candidate_count": 0,
        "network_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "canonical_packets_mutated": False,
        "operator_review_required": True,
    }


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _render_status_md(status):
    return "\n".join(
        [
            "# PMBOT SOURCE-008B Market Class Pilot Protocol Status",
            "",
            f"- task_id: {status['task_id']}",
            f"- status: {status['status']}",
            "- class_order: esports, weather, crypto",
            "- write_scope: protocol_status_or_dry_run_plan_artifacts_only",
            "- network_calls_performed: 0",
            "- openrouter_calls_performed: 0",
            "- polymarket_api_calls_performed: 0",
            "- real_ingested_template_count: "
            + str(status["current_source_state"]["real_ingested_template_count"]),
            "- draft_ingested_template_count: "
            + str(status["current_source_state"]["draft_ingested_template_count"]),
            "- ready_ingested_template_count: "
            + str(status["current_source_state"]["ready_ingested_template_count"]),
            "- future_live_002_allowed: false",
            "",
            "## Safety Boundary",
            "",
            "- no network calls",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no wallet or private key access",
            "- no orders",
            "- no runtime wiring",
            "- no dispatcher, background worker, queue, or browser automation",
            "- no canonical packet mutation",
            "- no probability, EV, edge, confidence, side selection, trade recommendation, buy, sell, hold, enter, exit, guaranteed win, free money, or sure bet labels",
            "",
        ]
    )


def _render_dry_run_md(plan):
    lines = [
        "# PMBOT SOURCE-008B Market Class Pilot Dry-Run Plan",
        "",
        f"- task_id: {plan['task_id']}",
        f"- status: {plan['status']}",
        "- class_order: esports, weather, crypto",
        f"- target_class_count: {plan['target_class_count']}",
        "- candidate_count: 0",
        "- network_calls_performed: 0",
        "- openrouter_calls_performed: 0",
        "- polymarket_api_calls_performed: 0",
        "- validator_status: " + plan["validation"]["validator_status"],
        "",
        "## Class Plans",
        "",
    ]
    for item in plan["class_plans"]:
        lines.extend(
            [
                f"- {item['market_class']}: {item['status']}",
                "  - required fields: " + ", ".join(item["required_capture_fields"]),
                "  - operator review required: true",
                "  - future fetch: separate approved read-only task only",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- no network calls",
            "- no data fetching",
            "- no candidate creation from live markets",
            "- no runtime, dispatcher, background worker, queue, or browser automation",
            "- no canonical packet mutation",
            "- no probability, EV, edge, confidence, side selection, trade recommendation, buy, sell, hold, enter, exit, guaranteed win, free money, or sure bet labels",
            "",
        ]
    )
    return "\n".join(lines)


def write_protocol_status(output_dir=OUTPUT_DIR, root=ROOT):
    status = build_protocol_status(root=root)
    output_root = _resolve(output_dir, root=root)
    _write_json(output_root / STATUS_JSON, status)
    (output_root / STATUS_MD).write_text(_render_status_md(status), encoding="utf-8")
    return status


def write_dry_run_plan(output_dir=OUTPUT_DIR, root=ROOT):
    plan = build_dry_run_plan(CLASS_ORDER, root=root)
    output_root = _resolve(output_dir, root=root)
    _write_json(output_root / DRY_RUN_JSON, plan)
    (output_root / DRY_RUN_MD).write_text(_render_dry_run_md(plan), encoding="utf-8")
    return plan


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Build SOURCE-008B market-class pilot protocol artifacts."
    )
    parser.add_argument("--protocol-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--class", dest="market_class", choices=CLASS_ORDER)
    parser.add_argument("--all-classes", action="store_true")
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    args = parser.parse_args(argv)

    requested_modes = sum(bool(item) for item in [args.protocol_only, args.dry_run, args.write])
    if requested_modes != 1:
        parser.error("choose exactly one of --protocol-only, --dry-run, or --write")
    if args.protocol_only and (args.market_class or args.all_classes):
        parser.error("--protocol-only does not accept class selection")
    if args.dry_run and not args.market_class:
        parser.error("--dry-run requires --class")
    if args.dry_run and args.all_classes:
        parser.error("--dry-run accepts one --class at a time")
    if args.write and not args.all_classes:
        parser.error("--write requires --all-classes")
    if args.write and args.market_class:
        parser.error("--write --all-classes does not accept --class")
    return args


def main(argv):
    args = _parse_args(argv)
    if args.protocol_only:
        status = build_protocol_status()
        print(json.dumps(status, indent=2, ensure_ascii=True))
        return 0
    if args.dry_run:
        plan = build_dry_run_plan((args.market_class,))
        print(json.dumps(plan, indent=2, ensure_ascii=True))
        return 0

    status = write_protocol_status(args.output_dir)
    plan = write_dry_run_plan(args.output_dir)
    print(
        json.dumps(
            {
                "schema_version": "market_class_pilot_write_result.v1",
                "task_id": TASK_ID,
                "status": "written",
                "protocol_status_path": str(Path(args.output_dir) / STATUS_JSON),
                "dry_run_plan_path": str(Path(args.output_dir) / DRY_RUN_JSON),
                "class_order": list(CLASS_ORDER),
                "target_class_count": plan["target_class_count"],
                "current_source_state": status["current_source_state"],
                "safety_summary": _base_safety_summary(),
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
