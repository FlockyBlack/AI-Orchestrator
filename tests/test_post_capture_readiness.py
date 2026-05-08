import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import export_post_capture_readiness as post_capture  # noqa: E402
from pm_bot.llm import ingest_manual_resolution_source_capture as ingest  # noqa: E402
REPORT = ROOT / "pm_bot" / "llm" / "post_capture_readiness_report.v1.json"
GATE = ROOT / "pm_bot" / "llm" / "post_capture_batch_readiness_gate.v1.json"


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
    path = (
        root
        / "pm_bot"
        / "llm"
        / "manual_resolution_source_capture"
        / f"{payload['market_id']}_resolution_source_capture.v1.json"
    )
    _write_json(path, payload)
    return path


def _write_readiness_before(root):
    _write_json(
        root
        / "pm_bot"
        / "llm"
        / "current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json",
        {
            "aggregate": {
                "updated_average_score": 0,
                "updated_high_count": 0,
                "updated_medium_count": 0,
                "updated_low_count": 0,
                "updated_blocked_count": 0,
            },
            "markets": [],
        },
    )


def _overlay_entry(payload):
    entry = {
        "market_id": payload["market_id"],
        "capture_path": (
            "pm_bot/llm/manual_resolution_source_capture/"
            f"{payload['market_id']}_resolution_source_capture.v1.json"
        ),
        "source_capture_status": payload["source_capture_status"],
        "capture_status": payload["capture_status"],
    }
    for field in ingest.REQUIRED_INGEST_FIELDS:
        entry[field] = payload.get(field)
    return entry


def _write_source005_artifacts(root, overlay_entries, real_filled_template_count=1):
    overlay = {
        "schema_version": ingest.OVERLAY_VERSION,
        "task_id": ingest.TASK_ID,
        "generated_by": ingest.GENERATED_BY,
        "status": "real_templates_ingested" if overlay_entries else "no_real_ingested_templates",
        "overlay_scope": "local_manual_source_capture_overlay_only",
        "canonical_packets_mutated": False,
        "real_ingested_template_count": len(overlay_entries),
        "markets": overlay_entries,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }
    result = {
        "schema_version": ingest.RESULT_VERSION,
        "task_id": ingest.TASK_ID,
        "generated_by": ingest.GENERATED_BY,
        "status": "completed" if overlay_entries else "blocked_or_pending",
        "ingest_status": "real_templates_ingested" if overlay_entries else "pending_manual_operator_filled_template",
        "reason": None if overlay_entries else "no eligible real filled manual capture templates",
        "dry_run": False,
        "include_drafts": True,
        "strict_ready": False,
        "real_filled_template_count": real_filled_template_count,
        "real_ingested_template_count": len(overlay_entries),
        "sandbox_example_count": 0,
        "skipped_empty_count": 13,
        "skipped_placeholder_count": 0,
        "skipped_example_count": 0,
        "overlay": overlay,
        "canonical_packets_mutated": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }
    _write_json(root / ingest.RESULT_JSON, result)
    _write_json(root / ingest.OVERLAY_JSON, overlay)


def test_post_capture_report_works_with_one_draft_overlay_market():
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert report["schema_version"] == "post_capture_readiness_report.v1"
    assert report["total_capture_templates"] == 15
    assert report["real_templates_not_started"] == 13
    assert report["real_templates_draft"] == 2
    assert report["real_filled_template_count"] == 2
    assert report["real_ingested_template_count"] == 2
    assert report["draft_ingested_template_count"] == 2
    assert report["ready_ingested_template_count"] == 0
    assert report["sandbox_example_count"] == 1
    assert report["markets_with_resolution_criteria_text"] == 2
    assert report["markets_with_full_resolution_rules"] == 2
    assert report["markets_with_official_source_references"] == 2
    assert report["markets_still_missing_resolution_criteria_text"] == 13
    assert report["markets_still_missing_full_resolution_rules"] == 13
    assert report["markets_still_missing_official_source_references"] == 13
    assert "1987056" in report["source_overlay_market_ids"]


def test_examples_do_not_increase_real_readiness(tmp_path):
    _write_readiness_before(tmp_path)
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

    report = post_capture.build_post_capture_readiness_report(tmp_path)

    assert report["sandbox_example_count"] == 1
    assert report["real_filled_template_count"] == 0
    assert report["real_ingested_template_count"] == 0
    assert report["readiness_after_if_available"]["available"] is False
    assert report["readiness_after_if_available"]["score_recalculation_performed"] is False


def test_gate_blocks_live_readonly_when_only_draft_overlay_is_ingested():
    gate = json.loads(GATE.read_text(encoding="utf-8"))

    assert gate["schema_version"] == "post_capture_batch_readiness_gate.v1"
    assert gate["live_readonly_api_discovery_readiness"] == "source_overlay_present_but_not_ready"
    assert gate["future_live_002_allowed"] is False
    assert gate["real_ingested_template_count"] == 2
    assert gate["draft_ingested_template_count"] == 2
    assert gate["ready_ingested_template_count"] == 0
    assert "no real manually ingested source capture templates" not in gate["blocker_reasons"]
    assert "ingested source capture exists only as draft" in gate["blocker_reasons"]
    assert "no ready_for_local_review or reviewed source capture templates" in gate["blocker_reasons"]
    assert "direct Polymarket rules verification still required" in gate["blocker_reasons"]
    assert "no explicit operator override document exists" in gate["blocker_reasons"]
    assert gate["queue_mutated"] is False
    assert gate["runtime_wiring_changed"] is False
    assert gate["dispatcher_changed"] is False
    assert gate["background_worker_created"] is False


def test_regression_source005_overlay_count_is_used_for_draft_ingest(tmp_path):
    _write_readiness_before(tmp_path)
    draft_packet = _packet(market_id="597964", status="draft", **_filled_fields())
    _write_packet(tmp_path, draft_packet)
    for index in range(13):
        _write_packet(tmp_path, _packet(market_id=f"empty-{index}", status="not_started"))
    _write_source005_artifacts(
        tmp_path,
        [_overlay_entry(draft_packet)],
        real_filled_template_count=1,
    )

    report = post_capture.build_post_capture_readiness_report(tmp_path)
    gate = report["gate"]

    assert report["overlay_read_by_readiness_exporter"] is True
    assert report["real_filled_template_count"] == 1
    assert report["real_ingested_template_count"] == 1
    assert report["draft_ingested_template_count"] == 1
    assert report["ready_ingested_template_count"] == 0
    assert report["markets_with_resolution_criteria_text"] == 1
    assert report["markets_with_full_resolution_rules"] == 1
    assert report["markets_with_official_source_references"] == 1
    assert report["markets_still_missing_resolution_criteria_text"] == 13
    assert report["markets_still_missing_full_resolution_rules"] == 13
    assert report["markets_still_missing_official_source_references"] == 13
    assert "no real manually ingested source capture templates" not in report["blocker_reasons"]
    assert report["readiness_after_if_available"]["available"] is True
    assert report["readiness_after_if_available"]["status"] == "source_overlay_present_but_not_ready"
    assert gate["future_live_002_allowed"] is False


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
