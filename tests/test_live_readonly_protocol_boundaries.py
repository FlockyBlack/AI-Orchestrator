import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_JSON = (
    ROOT / "pm_bot" / "live_readonly" / "polymarket_readonly_api_discovery_protocol.v1.json"
)
PLACEHOLDER = ROOT / "pm_bot" / "live_readonly" / "polymarket_readonly_discovery.py"


def test_protocol_json_exists_and_validates_core_boundaries():
    protocol = json.loads(PROTOCOL_JSON.read_text(encoding="utf-8"))

    assert protocol["schema_version"] == "polymarket_readonly_api_discovery_protocol.v1"
    assert protocol["status"] == "protocol_only_no_network"
    assert protocol["network_allowed_explicitly"] is False
    assert protocol["polymarket_api_calls_performed"] == 0
    assert protocol["external_network_calls_performed"] == 0
    safety = protocol["required_future_safety_fields"]
    assert safety["authenticated_endpoints_used"] is False
    assert safety["wallet_or_private_key_accessed"] is False
    assert safety["orders_created"] is False
    assert safety["runtime_wiring_changed"] is False
    assert safety["dispatcher_changed"] is False
    assert safety["background_worker_created"] is False
    assert safety["queue_mutated"] is False
    assert safety["browser_automation_used"] is False
    assert safety["operator_review_only"] is True
    assert safety["analysis_only"] is True


def test_future_network_tasks_require_explicit_approval():
    protocol = json.loads(PROTOCOL_JSON.read_text(encoding="utf-8"))

    assert protocol["future_task_separation"]["LIVE-001"]["network_approval_required"] is False
    for task_id in ("LIVE-002", "LIVE-003", "LIVE-004"):
        assert protocol["future_task_separation"][task_id]["network_approval_required"] is True
        assert protocol["future_task_separation"][task_id]["implemented_now"] is False
    assert protocol["readiness_gating"]["future_live_002_allowed_now"] is False
    assert protocol["readiness_gating"][
        "requires_real_ingested_capture_or_explicit_operator_override"
    ] is True


def test_placeholder_cli_is_protocol_only_and_zero_call():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.live_readonly.polymarket_readonly_discovery",
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
    assert payload["polymarket_api_calls_performed"] == 0
    assert payload["authenticated_endpoints_used"] is False
    assert payload["orders_created"] is False


def test_placeholder_module_has_no_network_client_imports():
    source = PLACEHOLDER.read_text(encoding="utf-8")
    forbidden_imports = (
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import aiohttp",
        "from aiohttp",
        "import socket",
        "import urllib",
    )
    for token in forbidden_imports:
        assert token not in source


def test_live_readonly_markdown_has_only_safety_context_action_terms():
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
    )
    paths = [
        ROOT / "docs" / "PMBOT_LIVE_001_READONLY_POLYMARKET_API_DISCOVERY_PROTOCOL.md",
        ROOT / "pm_bot" / "live_readonly" / "polymarket_readonly_api_discovery_protocol.v1.md",
        ROOT / "pm_bot" / "live_readonly" / "README.md",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            lowered = line.lower()
            for phrase in forbidden:
                if re.search(rf"\b{re.escape(phrase.lower())}\b", lowered):
                    assert any(marker in lowered for marker in safety_markers), (path, line)
