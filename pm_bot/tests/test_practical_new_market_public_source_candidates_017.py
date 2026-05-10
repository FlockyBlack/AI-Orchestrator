from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_plan_017")
FIXTURE_DIR = Path("pm_bot/tests/fixtures/new_market_public_evidence_plan_017")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_source_candidates_exist_for_bitcoin_market() -> None:
    candidates = _load(ARTIFACT_DIR / "new_market_public_source_candidates_017.json")

    assert (ARTIFACT_DIR / "new_market_public_source_candidates_017.md").exists()
    assert candidates["contract_version"] == "pmbot_new_market_public_source_candidates.v1"
    assert candidates["market_id"] == "573656"
    assert candidates["candidate_sources"]
    assert candidates["no_live_fetch_performed"] is True
    assert candidates["live_fetch_performed"] is False


def test_source_categories_are_safe_or_blocked_with_reason() -> None:
    candidates = _load(ARTIFACT_DIR / "new_market_public_source_candidates_017.json")

    for row in candidates["candidate_sources"]:
        assert row["reason"]
        assert row["live_fetch_performed"] is False
        assert row["requires_auth"] is False
        assert row["credentials_required"] is False
        assert row["cookies_required"] is False
        assert row["wallet_or_signing_required"] is False
        assert row["trading_or_order_endpoint"] is False
        assert row["allowed_by_registry"] is True or row["blocked"] is True
        if row["blocked"] is True:
            assert row["source_category_validation"]["reason"]


def test_missing_concrete_urls_are_reported_without_fake_urls() -> None:
    candidates = _load(ARTIFACT_DIR / "new_market_public_source_candidates_017.json")

    assert candidates["missing_concrete_urls"]
    assert all(row["reason"] for row in candidates["missing_concrete_urls"])
    assert all(
        row.get("concrete_public_url") in (None, "")
        for row in candidates["candidate_sources"]
        if row["url_status"] == "missing"
    )


def test_manual_url_mapping_fixture_is_missing_only_and_local() -> None:
    fixture = _load(FIXTURE_DIR / "new_market_public_url_mapping.manual_fixture.json")

    assert fixture["contract_version"] == "pmbot_new_market_public_url_mapping_manual_fixture.v1"
    assert fixture["market_id"] == "573656"
    assert fixture["live_fetch_performed"] is False
    assert fixture["mappings"]
    assert all(row["url_status"] == "missing" for row in fixture["mappings"])
    assert all(row["concrete_public_url"] is None for row in fixture["mappings"])
