import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import ingest_manual_resolution_source_capture as ingest  # noqa: E402


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _filled_fields():
    return {
        "full_market_resolution_criteria_text": "Local operator captured complete criteria text.",
        "full_resolution_rules": "Local operator captured complete rule clauses.",
        "official_source_references": ["Official local source label"],
        "official_source_urls_or_rule_references": ["local-rule-reference-1"],
        "source_timestamps": [
            {"source_label": "Official local source label", "checked_at_local": "2026-05-08T00:00:00+04:00"}
        ],
        "source_reliability_review": "Local operator reviewed source reliability and found it suitable for evidence completeness.",
        "reviewed_local_evidence_references": ["local/path/to/source_capture.json"],
        "non_placeholder_evidence_notes": "Local evidence notes are substantive and tied to the cited source label.",
    }


def _packet(market_id="123", status="not_started", **updates):
    payload = {
        "contract_version": "manual_resolution_source_capture.v1",
        "schema_version": "manual_resolution_source_capture_schema.v1",
        "market_id": market_id,
        "category": "test",
        "market_title_or_question": "Local test source capture?",
        "source_capture_status": status,
        "capture_status": status,
        "full_market_resolution_criteria_text": "",
        "full_resolution_rules": "",
        "official_source_references": [],
        "official_source_urls_or_rule_references": [],
        "source_timestamps": [],
        "source_reliability_review": "",
        "reviewed_local_evidence_references": [],
        "non_placeholder_evidence_notes": "",
        "no_market_action_guidance": True,
        "operator_review_only": True,
        "no_trading_authority": True,
        "no_queue_authority": True,
        "no_runtime_authority": True,
        "no_wallet_or_order_authority": True,
    }
    payload.update(updates)
    return payload


def _write_packet(root, payload):
    market_id = payload["market_id"]
    path = (
        root
        / "pm_bot"
        / "llm"
        / "manual_resolution_source_capture"
        / f"{market_id}_resolution_source_capture.v1.json"
    )
    _write_json(path, payload)
    return path


def test_empty_not_started_templates_are_skipped(tmp_path):
    _write_packet(tmp_path, _packet(status="not_started"))

    report = ingest.build_ingest_report(root=tmp_path)

    assert report["status"] == "blocked_or_pending"
    assert report["ingest_status"] == "pending_manual_operator_filled_template"
    assert report["real_filled_template_count"] == 0
    assert report["real_ingested_template_count"] == 0
    assert report["skipped_empty_count"] == 1
    assert report["template_results"][0]["skip_reason"] == "not_started_or_empty_template"


def test_sandbox_examples_are_skipped_and_counted_separately(tmp_path):
    _write_packet(tmp_path, _packet(status="not_started"))
    example = _packet(
        market_id="example_source",
        status="ready_for_local_review",
        example_only=True,
        sandbox_only=True,
        not_real_market_data=True,
        not_for_ingest_as_real_source=True,
        **_filled_fields(),
    )
    _write_json(
        tmp_path
        / "pm_bot"
        / "llm"
        / "manual_resolution_source_capture_examples"
        / "example_filled_capture.v1.json",
        example,
    )

    report = ingest.build_ingest_report(root=tmp_path, include_drafts=True)

    assert report["sandbox_example_count"] == 1
    assert report["skipped_example_count"] == 1
    assert report["real_filled_template_count"] == 0
    assert report["real_ingested_template_count"] == 0


def test_placeholder_fields_are_not_eligible(tmp_path):
    payload = _packet(status="ready_for_local_review", **_filled_fields())
    payload["full_resolution_rules"] = "TODO placeholder rules"
    _write_packet(tmp_path, payload)

    report = ingest.build_ingest_report(root=tmp_path)

    assert report["real_filled_template_count"] == 0
    assert report["real_ingested_template_count"] == 0
    assert report["skipped_placeholder_count"] == 1
    assert report["template_results"][0]["placeholder_required_source_fields"] == [
        "full_resolution_rules"
    ]


def test_draft_is_eligible_only_when_include_drafts_is_enabled(tmp_path):
    _write_packet(tmp_path, _packet(status="draft", **_filled_fields()))

    default_report = ingest.build_ingest_report(root=tmp_path)
    include_report = ingest.build_ingest_report(root=tmp_path, include_drafts=True)

    assert default_report["real_filled_template_count"] == 1
    assert default_report["real_ingested_template_count"] == 0
    assert default_report["template_results"][0]["skip_reason"] == (
        "status_not_allowed_by_current_cli_options"
    )
    assert include_report["real_ingested_template_count"] == 1


def test_strict_ready_excludes_filled_drafts(tmp_path):
    _write_packet(tmp_path, _packet(market_id="draft", status="draft", **_filled_fields()))
    _write_packet(
        tmp_path,
        _packet(market_id="ready", status="ready_for_local_review", **_filled_fields()),
    )

    report = ingest.build_ingest_report(
        root=tmp_path,
        include_drafts=True,
        strict_ready=True,
    )

    assert report["real_filled_template_count"] == 2
    assert report["real_ingested_template_count"] == 1
    assert report["overlay"]["markets"][0]["market_id"] == "ready"


def test_no_eligible_templates_produces_pending_status_not_failure(tmp_path):
    _write_packet(tmp_path, _packet(status="not_started"))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.llm.ingest_manual_resolution_source_capture",
            "--dry-run",
            "--summary-only",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    summary = json.loads(result.stdout)

    assert summary["status"] == "blocked_or_pending"
    assert summary["ingest_status"] == "pending_manual_operator_filled_template"
    assert summary["reason"] == "no eligible real filled manual capture templates"


def test_ingest_module_has_no_network_imports():
    source = (ROOT / "pm_bot" / "llm" / "ingest_manual_resolution_source_capture.py").read_text(
        encoding="utf-8"
    )
    forbidden_imports = ("requests", "httpx", "socket", "urllib", "aiohttp")
    for token in forbidden_imports:
        assert token not in source


def test_generated_source_005_public_docs_have_only_safety_context_action_terms():
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
        ROOT / "docs" / "PMBOT_SOURCE_005_MANUAL_CAPTURE_INGEST_FROM_FILLED_TEMPLATES.md",
        ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_ingest_result.v1.md",
        ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_ingest_manifest.v1.md",
        ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_ingested_overlay.v1.md",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            lowered = line.lower()
            for phrase in forbidden:
                if re.search(rf"\b{re.escape(phrase.lower())}\b", lowered):
                    assert any(marker in lowered for marker in safety_markers), (path, line)
