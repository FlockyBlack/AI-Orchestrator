from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_plan_017")


def _load(name: str) -> dict:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def test_new_market_fetch_manifest_exists_and_is_capped() -> None:
    manifest = _load("new_market_fetch_request_manifest_017.json")

    assert (ARTIFACT_DIR / "new_market_fetch_request_manifest_017.md").exists()
    assert manifest["contract_version"] == "pmbot_new_market_fetch_request_manifest.v1"
    assert manifest["market_id"] == "573656"
    assert len(manifest["request_intents"]) <= 3
    assert manifest["max_request_count"] == 3
    assert manifest["within_request_limit"] is True


def test_manifest_counts_are_consistent_and_local_only() -> None:
    manifest = _load("new_market_fetch_request_manifest_017.json")

    assert manifest["executable_request_count"] == len(manifest["executable_request_intents"])
    assert manifest["missing_url_count"] == len(manifest["missing_url_request_intents"])
    assert manifest["blocked_request_count"] == len(manifest["blocked_request_intents"])
    assert manifest["executable_request_count"] + manifest["missing_url_count"] + manifest["blocked_request_count"] == len(
        manifest["request_intents"]
    )
    assert manifest["executable_request_count"] <= manifest["max_request_count"]
    assert manifest["live_fetch_performed"] is False
    assert manifest["operator_approval_required_before_fetch"] is True


def test_missing_executable_blocked_request_buckets_are_expected() -> None:
    manifest = _load("new_market_fetch_request_manifest_017.json")

    assert manifest["executable_request_count"] == 0
    assert manifest["missing_url_count"] == 3
    assert manifest["blocked_request_count"] == 0
    assert all(row["url_status"] == "missing" for row in manifest["missing_url_request_intents"])


def test_url_safety_report_exists_and_reports_missing_urls() -> None:
    report = _load("new_market_url_safety_report_017.json")

    assert (ARTIFACT_DIR / "new_market_url_safety_report_017.md").exists()
    assert report["contract_version"] == "pmbot_new_market_url_safety_report.v1"
    assert report["checked_request_count"] == 3
    assert report["allowed_count"] == 0
    assert report["blocked_count"] == 0
    assert report["missing_url_count"] == 3
    assert report["live_fetch_performed"] is False
    assert all(row["url_status"] == "missing" for row in report["per_request_safety"])


def test_preflight_dry_run_blocks_execution_without_urls_and_approval() -> None:
    preflight = _load("new_market_fetch_preflight_dry_run_017.result.json")

    assert preflight["ready_to_execute_public_read_only_fetch"] is False
    assert preflight["would_be_ready_after_operator_approval"] is False
    assert preflight["approval_required"] is True
    assert preflight["approval_granted"] is False
    assert preflight["executable_request_count"] == 0
    assert preflight["missing_url_count"] == 3
    assert "no concrete safe public URLs" in preflight["blockers"]
