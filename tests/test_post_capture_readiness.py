import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import export_post_capture_readiness as post_capture  # noqa: E402
REPORT = ROOT / "pm_bot" / "llm" / "post_capture_readiness_report.v1.json"
GATE = ROOT / "pm_bot" / "llm" / "post_capture_batch_readiness_gate.v1.json"


def test_post_capture_report_works_with_zero_real_filled_templates():
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert report["schema_version"] == "post_capture_readiness_report.v1"
    assert report["total_capture_templates"] == 14
    assert report["real_templates_not_started"] == 14
    assert report["real_filled_template_count"] == 0
    assert report["real_ingested_template_count"] == 0
    assert report["sandbox_example_count"] == 1
    assert report["markets_with_resolution_criteria_text"] == 0
    assert report["markets_with_full_resolution_rules"] == 0
    assert report["markets_with_official_source_references"] == 0
    assert report["markets_still_missing_resolution_criteria_text"] == 14
    assert report["markets_still_missing_full_resolution_rules"] == 14
    assert report["markets_still_missing_official_source_references"] == 14


def test_examples_do_not_increase_real_readiness():
    report = post_capture.build_post_capture_readiness_report(ROOT)

    assert report["sandbox_example_count"] == 1
    assert report["real_filled_template_count"] == 0
    assert report["real_ingested_template_count"] == 0
    assert report["readiness_after_if_available"]["available"] is False
    assert report["readiness_after_if_available"]["score_recalculation_performed"] is False


def test_gate_blocks_live_readonly_when_real_filled_count_is_zero():
    gate = json.loads(GATE.read_text(encoding="utf-8"))

    assert gate["schema_version"] == "post_capture_batch_readiness_gate.v1"
    assert gate["live_readonly_api_discovery_readiness"] == "not_ready"
    assert gate["future_live_002_allowed"] is False
    assert "no real manually filled source capture templates" in gate["blocker_reasons"]
    assert gate["queue_mutated"] is False
    assert gate["runtime_wiring_changed"] is False
    assert gate["dispatcher_changed"] is False
    assert gate["background_worker_created"] is False


def test_post_capture_generated_json_is_valid():
    paths = [
        ROOT / "pm_bot" / "llm" / "post_capture_readiness_report.v1.json",
        ROOT / "pm_bot" / "llm" / "post_capture_batch_readiness_gate.v1.json",
        ROOT / "docs" / "PMBOT_SOURCE_006_RESULT.json",
    ]
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict), path


def test_source_006_public_markdown_has_only_safety_context_action_terms():
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
    safety_markers = ("no ", "not ", "never", "prohibited", "forbidden", "without")
    paths = [
        ROOT / "docs" / "PMBOT_SOURCE_006_POST_CAPTURE_READINESS_AND_BATCH_GATE_REFRESH.md",
        ROOT / "pm_bot" / "llm" / "post_capture_readiness_report.v1.md",
        ROOT / "pm_bot" / "llm" / "post_capture_batch_readiness_gate.v1.md",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            lowered = line.lower()
            for phrase in forbidden:
                if re.search(rf"\b{re.escape(phrase.lower())}\b", lowered):
                    assert any(marker in lowered for marker in safety_markers), (path, line)
