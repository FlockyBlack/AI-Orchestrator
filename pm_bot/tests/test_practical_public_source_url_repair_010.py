from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.public_source_registry import validate_source_category
from pm_bot.practical.public_source_url_repair import (
    DEFAULT_009_DIR,
    DEFAULT_ENRICHED_MANIFEST,
    DEFAULT_MAPPING_FIXTURE,
    build_public_source_url_repair,
    build_repaired_manifest_url_safety_report,
    build_repaired_public_fetch_manifest,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture_repairs() -> list[dict]:
    return _load(DEFAULT_MAPPING_FIXTURE)["repairs"]


def _repair() -> dict:
    return build_public_source_url_repair(
        failure_diagnosis=_load(DEFAULT_009_DIR / "public_fetch_failure_diagnosis_009.json"),
        fix_packet=_load(DEFAULT_009_DIR / "failed_source_url_fix_packet_009.json"),
        source_learning=_load(DEFAULT_009_DIR / "source_accessibility_learning_009.json"),
        enriched_manifest=_load(DEFAULT_ENRICHED_MANIFEST),
        repair_mapping=_fixture_repairs(),
        generated_at="2026-05-10T00:00:00Z",
    )


def test_failed_requests_from_practical_009_are_loaded() -> None:
    repair = _repair()

    assert repair["contract_version"] == "pmbot_public_source_url_repair.v1"
    assert repair["input_failed_request_count"] == 4
    assert {row["request_intent_id"] for row in repair["repaired_request_intents"]} == {
        "public_fetch_request_intent_006_06_598936_598936_domain_public_evidence",
        "public_fetch_request_intent_006_04_597964_597964_domain_public_evidence",
        "public_fetch_request_intent_006_08_691547_691547_domain_public_evidence",
        "public_fetch_request_intent_006_10_692258_692258_domain_public_evidence",
    }


def test_repair_manifest_is_created_and_categories_work() -> None:
    repair = _repair()
    manifest = build_repaired_public_fetch_manifest(repair)

    assert manifest["contract_version"] == "pmbot_repaired_public_fetch_manifest.v1"
    assert manifest["executable_request_count"] == 1
    assert len(manifest["no_retry_request_intents"]) == 1
    assert len(manifest["replacement_missing_request_intents"]) == 1
    assert len(manifest["blocked_request_intents"]) == 1
    assert manifest["executable_request_intents"][0]["source_url"] == "https://blog.kraken.com/"


def test_request_count_is_capped_and_repair_does_not_fetch() -> None:
    repair = _repair()
    manifest = build_repaired_public_fetch_manifest(repair, max_request_count=5)

    assert manifest["executable_request_count"] <= 5
    assert manifest["max_request_count"] == 5
    assert manifest["within_request_limit"] is True
    assert repair["live_fetch_performed"] is False
    assert manifest["live_fetch_performed"] is False


def test_no_unsafe_url_category_becomes_executable() -> None:
    repair = _repair()
    manifest = build_repaired_public_fetch_manifest(repair)
    safety = build_repaired_manifest_url_safety_report(manifest)

    assert safety["allowed_count"] == manifest["executable_request_count"]
    assert safety["blocked_count"] == 0
    for row in manifest["executable_request_intents"]:
        category = validate_source_category(row["source_category"])
        assert category["blocked"] is False
        assert row["requires_auth"] is False
        assert row["cookies_required"] is False
        assert row["wallet_or_signing_required"] is False
        assert row["trading_or_order_endpoint"] is False
