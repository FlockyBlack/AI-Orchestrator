from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/paper_update_application_012")
APPROVAL_JSON = ARTIFACT_DIR / "paper_update_operator_approval_012.json"
APPROVAL_MD = ARTIFACT_DIR / "paper_update_operator_approval_012.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_approval_artifact_exists_and_validates() -> None:
    approval = _load(APPROVAL_JSON)

    assert APPROVAL_MD.exists()
    assert approval["contract_version"] == "pmbot_paper_update_operator_approval.v1"
    assert approval["approval_status"] == "approved_for_paper_tracking_update_only"
    assert approval["approved_by"] == "operator"
    assert approval["reusable"] is False
    assert approval["expires_after_task"] is True
    assert approval["approved_update_candidate_ids"] == ["paper-hypothesis-update-candidate-009"]
    assert approval["approved_market_ids"] == ["563650"]
    assert approval["approved_hypothesis_ids"] == ["563650.analysis.adc53630aa1f.paper_hypothesis"]


def test_approval_scope_is_paper_only() -> None:
    approval = _load(APPROVAL_JSON)
    scope = set(approval["approval_scope"])

    assert "paper_tracking_update_only" in scope
    assert "non_executable" in scope
    assert "no_real_trade_decision" in scope
    assert "no_orders" in scope
    assert "no_wallet" in scope
    assert "no_trading" in scope
    assert "original_artifacts_preserved" in scope
    assert "versioned_snapshot_required" in scope


def test_blocked_scope_includes_trading_wallet_and_orders() -> None:
    approval = _load(APPROVAL_JSON)
    blocked = " ".join(approval["blocked_scope"]).lower()

    assert "real trading" in blocked
    assert "wallet/signing/orders" in blocked
    assert "trading recommendations" in blocked
    assert "probability/ev/edge/side-selection trading signal" in blocked
    assert "automatic market action" in blocked
