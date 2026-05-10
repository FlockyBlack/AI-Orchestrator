from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.practical.public_fetch_execution_preflight import (
    build_second_fetch_preflight,
    validate_second_fetch_scoped_approval,
)
from pm_bot.practical.public_source_url_repair import (
    DEFAULT_009_DIR,
    DEFAULT_ENRICHED_MANIFEST,
    DEFAULT_MAPPING_FIXTURE,
    build_public_source_url_repair,
    build_repaired_manifest_url_safety_report,
    build_repaired_public_fetch_manifest,
    build_second_fetch_approval,
    execute_second_controlled_fetch_packet,
)
from pm_bot.practical.saved_public_evidence_packet import assert_valid_saved_public_evidence_packet

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_source_url_fixes_010")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest() -> dict:
    mapping = _load(DEFAULT_MAPPING_FIXTURE)["repairs"]
    repair = build_public_source_url_repair(
        failure_diagnosis=_load(DEFAULT_009_DIR / "public_fetch_failure_diagnosis_009.json"),
        fix_packet=_load(DEFAULT_009_DIR / "failed_source_url_fix_packet_009.json"),
        source_learning=_load(DEFAULT_009_DIR / "source_accessibility_learning_009.json"),
        enriched_manifest=_load(DEFAULT_ENRICHED_MANIFEST),
        repair_mapping=mapping,
        generated_at="2026-05-10T00:00:00Z",
    )
    return build_repaired_public_fetch_manifest(repair)


def _fixture_fetcher(intent: Mapping[str, Any], _safety: Mapping[str, Any]) -> dict:
    return {
        "status_code": 200,
        "final_url": intent["source_url"],
        "headers": {"Content-Type": "text/plain"},
        "body": b"public fixture body for second controlled fetch",
    }


def test_scoped_approval_validates() -> None:
    manifest = _manifest()
    approval = build_second_fetch_approval(manifest, generated_at="2026-05-10T00:00:00Z")
    validation = validate_second_fetch_scoped_approval(approval, manifest)

    assert validation["valid"] is True
    assert approval["approval_status"] == "approved_for_scoped_public_read_only_fetch_only"
    assert approval["max_request_count"] == 5
    assert approval["method_allowed"] == "GET"
    assert approval["automatic_analysis_update_allowed"] is False


def test_second_fetch_preflight_exists_and_request_count_is_bounded() -> None:
    preflight = _load(ARTIFACT_DIR / "second_fetch_preflight_010.result.json")

    assert preflight["contract_version"] == "pmbot_second_controlled_public_fetch_preflight.v1"
    assert preflight["executable_request_count"] <= 5
    assert preflight["approved_request_count"] <= 5
    assert preflight["within_request_limit"] is True
    assert preflight["live_fetch_performed"] is False


def test_execution_only_eligible_if_preflight_ready(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["executable_request_intents"] = []
    manifest["executable_request_count"] = 0
    approval = build_second_fetch_approval(manifest, generated_at="2026-05-10T00:00:00Z")
    safety = build_repaired_manifest_url_safety_report(manifest)
    preflight = build_second_fetch_preflight(
        repaired_manifest=manifest,
        approval=approval,
        safety_report=safety,
    )

    summary = execute_second_controlled_fetch_packet(
        manifest=manifest,
        preflight=preflight,
        out_dir=tmp_path,
        fetcher=_fixture_fetcher,
        fixture_mode=True,
    )

    assert preflight["ready_to_execute_public_read_only_fetch"] is False
    assert summary["live_fetch_performed"] is False
    assert summary["request_count_attempted"] == 0
    assert (tmp_path / "evidence_packets" / "no_evidence_created_second_fetch.json").exists()


def test_fixture_success_creates_valid_evidence_packet(tmp_path: Path) -> None:
    manifest = _manifest()
    approval = build_second_fetch_approval(manifest, generated_at="2026-05-10T00:00:00Z")
    safety = build_repaired_manifest_url_safety_report(manifest, fixture_mode=True)
    preflight = build_second_fetch_preflight(
        repaired_manifest=manifest,
        approval=approval,
        safety_report=safety,
        fixture_mode=True,
    )

    summary = execute_second_controlled_fetch_packet(
        manifest=manifest,
        preflight=preflight,
        out_dir=tmp_path,
        fetcher=_fixture_fetcher,
        fixture_mode=True,
    )

    assert summary["request_count_attempted"] == 1
    assert summary["request_count_succeeded"] == 1
    assert summary["evidence_packets_created_count"] == 1
    packet = _load(Path(summary["evidence_packets_created"][0]))
    assert_valid_saved_public_evidence_packet(packet)
    assert packet["capture_mode"] == "fixture"
    assert packet["live_network_used"] is False
    assert packet["http_status"] == 200


def test_automatic_analysis_update_remains_false() -> None:
    summary = _load(ARTIFACT_DIR / "second_fetch_execution_summary_010.result.json")

    assert summary["safety_summary"]["openrouter_calls_performed"] == 0
    assert summary["safety_summary"]["authenticated_endpoints_used"] is False
    assert summary["safety_summary"]["wallet_or_private_key_access"] is False
    assert summary["safety_summary"]["orders_or_trading_actions"] is False
    assert summary["safety_summary"]["market_recommendation_generated"] is False
    assert summary["safety_summary"]["probability_ev_edge_or_side_selection_generated"] is False
