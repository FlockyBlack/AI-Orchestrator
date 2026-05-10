from __future__ import annotations

import json
import re
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/daily_workflow_015")
CHECKLIST_JSON = ARTIFACT_DIR / "practical_daily_checklist_015.json"
QUICKSTART_JSON = ARTIFACT_DIR / "operator_quickstart_card_015.json"
MATRIX_JSON = ARTIFACT_DIR / "next_task_decision_matrix_015.json"
STATUS_JSON = ARTIFACT_DIR / "current_practical_status_snapshot_015.json"
BOUNDARY_JSON = ARTIFACT_DIR / "practical_safety_boundary_reference_015.json"

RUNBOOK_DOC = Path("docs/PMBOT_PRACTICAL_DAILY_OPERATOR_RUNBOOK.md")
ADD_MARKET_DOC = Path("docs/PMBOT_HOW_TO_ADD_A_NEW_LOCAL_MARKET_PACKET.md")
PROCESS_OUTCOME_DOC = Path("docs/PMBOT_HOW_TO_PROCESS_A_RESOLVED_MARKET_OUTCOME.md")

ACTIONABLE_MARKET_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\b.{0,80}"
    r"\b(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)
QUANT_SIGNAL_PATTERN = re.compile(
    r"\b(?:probability|ev|edge|confidence)\b.{0,40}\b(?:signal|instruction)\b",
    re.IGNORECASE,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_checklist_and_operator_artifacts_exist() -> None:
    checklist = _load(CHECKLIST_JSON)
    quickstart = _load(QUICKSTART_JSON)
    matrix = _load(MATRIX_JSON)
    status = _load(STATUS_JSON)
    boundary = _load(BOUNDARY_JSON)

    assert (ARTIFACT_DIR / "practical_daily_checklist_015.md").exists()
    assert (ARTIFACT_DIR / "operator_quickstart_card_015.md").exists()
    assert (ARTIFACT_DIR / "next_task_decision_matrix_015.md").exists()
    assert (ARTIFACT_DIR / "current_practical_status_snapshot_015.md").exists()
    assert (ARTIFACT_DIR / "practical_safety_boundary_reference_015.md").exists()
    assert checklist["contract_version"] == "pmbot_practical_daily_checklist.v1"
    assert quickstart["contract_version"] == "pmbot_operator_quickstart_card.v1"
    assert matrix["contract_version"] == "pmbot_next_task_decision_matrix.v1"
    assert status["contract_version"] == "pmbot_current_practical_status_snapshot.v1"
    assert boundary["contract_version"] == "pmbot_practical_safety_boundary_reference.v1"


def test_runbook_docs_exist() -> None:
    assert RUNBOOK_DOC.exists()
    assert ADD_MARKET_DOC.exists()
    assert PROCESS_OUTCOME_DOC.exists()


def test_status_snapshot_keeps_real_autonomous_trading_at_zero() -> None:
    status = _load(STATUS_JSON)

    assert status["real_autonomous_trading_progress_estimate"] == "0%"
    assert status["tracked_market_count"] == 5
    assert status["unresolved_outcome_count"] == 5
    assert status["feedback_ready_count"] == 0
    assert status["evidence_packet_count"] == 2
    assert status["applied_paper_update_count"] == 1
    assert status["source_records_count"] == 5


def test_safety_boundary_reference_lists_required_boundaries() -> None:
    boundary = _load(BOUNDARY_JSON)
    text = "\n".join(boundary["boundaries"]).lower()

    assert "wallet" in text
    assert "private key" in text
    assert "order placement" in text
    assert "trading endpoints" in text
    assert "real-money action" in text
    assert "authenticated endpoint" in text
    assert "openrouter" in text
    assert "polymarket api" in text
    assert "scheduler" in text
    assert "paper-only tracking" in text


def test_docs_and_artifacts_do_not_contain_actionable_trading_language() -> None:
    paths = [
        ARTIFACT_DIR / "daily_workflow_summary_015.md",
        ARTIFACT_DIR / "operator_quickstart_card_015.md",
        ARTIFACT_DIR / "next_task_decision_matrix_015.md",
        ARTIFACT_DIR / "practical_safety_boundary_reference_015.md",
        RUNBOOK_DOC,
        ADD_MARKET_DOC,
        PROCESS_OUTCOME_DOC,
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert ACTIONABLE_MARKET_PATTERN.search(text) is None, path
        assert QUANT_SIGNAL_PATTERN.search(text) is None, path
