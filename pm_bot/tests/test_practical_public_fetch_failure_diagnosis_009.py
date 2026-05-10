from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_review_009")
DIAGNOSIS_JSON = ARTIFACT_DIR / "public_fetch_failure_diagnosis_009.json"
DIAGNOSIS_MD = ARTIFACT_DIR / "public_fetch_failure_diagnosis_009.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_public_fetch_failure_diagnosis_artifact_exists() -> None:
    diagnosis = _load(DIAGNOSIS_JSON)

    assert DIAGNOSIS_MD.exists()
    assert diagnosis["contract_version"] == "pmbot_public_fetch_failure_diagnosis.v1"
    assert diagnosis["diagnosis_id"] == "public-fetch-failure-diagnosis-009"


def test_public_fetch_failure_diagnosis_counts_match_practical_008() -> None:
    diagnosis = _load(DIAGNOSIS_JSON)

    assert diagnosis["attempted_request_count"] == 5
    assert diagnosis["failed_request_count"] == 4
    assert diagnosis["succeeded_request_count"] == 1
    assert diagnosis["blocked_request_count"] == 0
    assert len(diagnosis["per_request_diagnosis"]) == 4


def test_public_fetch_failure_diagnosis_includes_safe_recovery_actions() -> None:
    diagnosis = _load(DIAGNOSIS_JSON)

    assert diagnosis["safe_recovery_actions"]
    assert diagnosis["url_manifest_fix_candidates"]
    assert diagnosis["do_not_retry_without_review"] is True
    assert diagnosis["no_live_fetch_performed_in_this_task"] is True


def test_public_fetch_failure_diagnosis_safety_flags_are_safe() -> None:
    diagnosis = _load(DIAGNOSIS_JSON)

    assert diagnosis["no_real_trade_decision"] is True
    assert diagnosis["market_recommendation_generated"] is False
    assert diagnosis["probability_ev_edge_or_side_selection_generated"] is False
    assert diagnosis["orders_or_trading_actions"] is False
    assert diagnosis["wallet_or_private_key_access"] is False
