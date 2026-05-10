from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011")
LINKS_JSON = ARTIFACT_DIR / "public_evidence_hypothesis_links_011.json"
LINKS_MD = ARTIFACT_DIR / "public_evidence_hypothesis_links_011.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_evidence_hypothesis_links_are_generated() -> None:
    links = _load(LINKS_JSON)

    assert LINKS_MD.exists()
    assert links["contract_version"] == "pmbot_public_evidence_hypothesis_links.v1"
    assert links["links"]
    assert links["operator_review_required"] is True


def test_links_connect_evidence_market_hypothesis_and_update_candidate() -> None:
    links = _load(LINKS_JSON)

    linked_market_ids = {row["market_id"] for row in links["links"]}
    linked_hypothesis_ids = {row["hypothesis_id"] for row in links["links"]}
    assert {"563650", "691547"}.issubset(linked_market_ids)
    assert any(hypothesis_id.startswith("563650.") for hypothesis_id in linked_hypothesis_ids)
    assert any(row["update_candidate_status"] == "pending_operator_review" for row in links["links"])


def test_unlinked_and_missing_evidence_buckets_are_reported() -> None:
    links = _load(LINKS_JSON)

    assert "unlinked_evidence_packets" in links
    assert "hypotheses_without_public_evidence" in links
    assert "markets_without_public_evidence" in links
    assert len(links["hypotheses_without_public_evidence"]) >= 3
    assert len(links["markets_without_public_evidence"]) >= 3
