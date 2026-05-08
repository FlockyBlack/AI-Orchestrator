import ast
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_JSON = ROOT / "pm_bot" / "live_readonly" / "market_rules_capture_protocol.v1.json"
PROTOCOL_MD = ROOT / "pm_bot" / "live_readonly" / "market_rules_capture_protocol.v1.md"
PLACEHOLDER = ROOT / "pm_bot" / "live_readonly" / "market_rules_capture_pipeline.py"
RAW_SCHEMA = ROOT / "pm_bot" / "live_readonly" / "schemas" / "market_rules_raw_fetch.schema.v1.json"
NORMALIZED_SCHEMA = (
    ROOT
    / "pm_bot"
    / "live_readonly"
    / "schemas"
    / "market_rules_normalized_candidate.schema.v1.json"
)
AUTO_FILL_SCHEMA = (
    ROOT / "pm_bot" / "live_readonly" / "schemas" / "market_rules_auto_fill_plan.schema.v1.json"
)
SOURCE_008_RESULT = ROOT / "docs" / "PMBOT_SOURCE_008_RESULT.json"

EXPECTED_MARKETS = [
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
]


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_protocol_artifacts_exist_and_are_valid_json():
    for path in [PROTOCOL_JSON, RAW_SCHEMA, NORMALIZED_SCHEMA, AUTO_FILL_SCHEMA, SOURCE_008_RESULT]:
        payload = _load_json(path)
        assert isinstance(payload, dict), path

    protocol = _load_json(PROTOCOL_JSON)
    assert protocol["schema_version"] == "market_rules_capture_protocol.v1"
    assert protocol["status"] == "protocol_only_no_network"
    assert protocol["current_stage"] == "STAGE_0_PROTOCOL_ONLY"
    assert protocol["current_market_ids"] == EXPECTED_MARKETS
    assert protocol["network_allowed_explicitly"] is False
    assert protocol["polymarket_api_calls_performed"] == 0


def test_placeholder_cli_protocol_only_exits_successfully():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.live_readonly.market_rules_capture_pipeline",
            "--protocol-only",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload["status"] == "protocol_only_no_network"
    assert payload["network_allowed_explicitly"] is False
    assert payload["network_calls_performed"] == 0
    assert payload["polymarket_api_calls_performed"] == 0
    assert payload["authenticated_endpoints_used"] is False
    assert payload["wallet_or_private_key_accessed"] is False


def test_placeholder_cli_market_dry_run_does_not_perform_network():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.live_readonly.market_rules_capture_pipeline",
            "--dry-run",
            "--market-id",
            "597964",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload["status"] == "dry_run_planned_not_fetched"
    assert payload["target_market_ids"] == ["597964"]
    assert payload["network_calls_performed"] == 0
    assert payload["polymarket_api_calls_performed"] == 0
    assert payload["fetch_performed"] is False
    assert payload["validation"]["validator_status"] == "passed"
    market_plan = payload["market_plans"][0]
    assert market_plan["status"] == "planned_not_fetched"
    assert market_plan["planned_status_after_fill"] == "draft"
    assert market_plan["will_auto_promote_to_ready"] is False
    assert market_plan["canonical_packets_mutated"] is False


def test_placeholder_cli_all_current_markets_lists_exactly_14_known_markets():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.live_readonly.market_rules_capture_pipeline",
            "--dry-run",
            "--all-current-markets",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload["target_market_count"] == 14
    assert payload["target_market_ids"] == EXPECTED_MARKETS
    assert [item["market_id"] for item in payload["market_plans"]] == EXPECTED_MARKETS
    assert {item["status"] for item in payload["market_plans"]} == {"planned_not_fetched"}


def test_placeholder_module_has_no_network_or_browser_client_imports():
    tree = ast.parse(PLACEHOLDER.read_text(encoding="utf-8"))
    forbidden_roots = {
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "selenium",
        "playwright",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_roots
        if isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root not in forbidden_roots

    source = PLACEHOLDER.read_text(encoding="utf-8")
    for token in ("openrouter_api_key", "bearer "):
        assert token not in source.lower()


def test_future_auto_fill_plan_is_draft_only():
    protocol = _load_json(PROTOCOL_JSON)
    schema = _load_json(AUTO_FILL_SCHEMA)

    guardrails = protocol["auto_fill_guardrails"]
    assert guardrails["planned_status_after_fill"] == "draft"
    assert guardrails["source_capture_status_after_fill"] == "draft"
    assert guardrails["capture_status_after_fill"] == "draft"
    assert guardrails["will_auto_promote_to_ready"] is False
    assert guardrails["forbidden_auto_statuses"] == ["ready_for_local_review", "reviewed"]
    assert guardrails["canonical_packets_mutated"] is False

    properties = schema["properties"]
    assert properties["planned_status_after_fill"]["const"] == "draft"
    assert properties["will_auto_promote_to_ready"]["const"] is False
    assert properties["canonical_packets_mutated"]["const"] is False
    assert properties["operator_review_required"]["const"] is True


def test_protocol_forbids_wallet_orders_runtime_dispatcher_background_queue_and_browser():
    protocol = _load_json(PROTOCOL_JSON)
    safety = protocol["required_future_safety_fields"]

    assert safety["authenticated_endpoints_used"] is False
    assert safety["wallet_or_private_key_accessed"] is False
    assert safety["orders_created"] is False
    assert safety["trading_runtime_changed"] is False
    assert safety["dispatcher_changed"] is False
    assert safety["background_worker_created"] is False
    assert safety["queue_mutated"] is False
    assert safety["browser_automation_used"] is False
    assert safety["canonical_packets_mutated"] is False
    assert safety["operator_review_only"] is True
    assert safety["analysis_only"] is True


def test_protocol_and_contracts_do_not_define_market_prediction_fields():
    protocol = _load_json(PROTOCOL_JSON)
    normalized_schema = _load_json(NORMALIZED_SCHEMA)
    auto_fill_schema = _load_json(AUTO_FILL_SCHEMA)
    allowed_false_safety_fields = {
        "probability_ev_edge_confidence_generated",
        "side_selection_generated",
    }

    assert protocol["required_future_safety_fields"]["probability_ev_edge_confidence_generated"] is False
    assert protocol["required_future_safety_fields"]["side_selection_generated"] is False

    for schema in [normalized_schema, auto_fill_schema]:
        properties = schema["properties"]
        forbidden_exact_fields = {
            "probability",
            "ev",
            "edge",
            "confidence",
            "confidence_score",
            "betting_confidence",
            "side_selection",
            "recommended_side",
        }
        assert forbidden_exact_fields.isdisjoint({key.lower() for key in properties})
        safety_properties = properties.get("safety_summary", {}).get("properties", {})
        for key, value in safety_properties.items():
            if key in allowed_false_safety_fields:
                assert value["const"] is False


def test_generated_public_markdown_has_only_safety_context_action_terms():
    forbidden = [
        "buy",
        "sell",
        "hold",
        "enter",
        "exit",
        "long",
        "short",
        "take profit",
        "stop loss",
        "edge",
        "EV",
        "expected value",
        "confidence score",
        "side selection",
        "recommended trade",
        "trading approval",
        "autonomous trading",
    ]
    safety_markers = (
        "no ",
        "not ",
        "never",
        "prohibited",
        "forbidden",
        "without",
        "blocked",
        "does not",
    )
    paths = [
        PROTOCOL_MD,
        ROOT / "docs" / "PMBOT_SOURCE_008_READONLY_MARKET_RULES_CAPTURE_PIPELINE_PROTOCOL.md",
        ROOT / "docs" / "PMBOT_SOURCE_NEXT_STEPS_AFTER_008.md",
        ROOT / "pm_bot" / "live_readonly" / "README.md",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            lowered = line.lower()
            for phrase in forbidden:
                if re.search(rf"\b{re.escape(phrase.lower())}\b", lowered):
                    assert any(marker in lowered for marker in safety_markers), (path, line)


def test_existing_source_007_state_remains_intact():
    ingest_result = _load_json(
        ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_ingest_result.v1.json"
    )
    capture_597964 = _load_json(
        ROOT
        / "pm_bot"
        / "llm"
        / "manual_resolution_source_capture"
        / "597964_resolution_source_capture.v1.json"
    )
    gate = _load_json(ROOT / "pm_bot" / "llm" / "post_capture_batch_readiness_gate.v1.json")

    assert ingest_result["real_ingested_template_count"] >= 1
    assert ingest_result["overlay"]["real_ingested_template_count"] >= 1
    assert capture_597964["source_capture_status"] == "draft"
    assert capture_597964["capture_status"] == "draft"
    assert gate["real_ingested_template_count"] >= 1
    assert gate["draft_ingested_template_count"] >= 1
    assert gate["ready_ingested_template_count"] == 0
    assert gate["future_live_002_allowed"] is False
    assert gate["live_readonly_api_discovery_readiness"] == "source_overlay_present_but_not_ready"
