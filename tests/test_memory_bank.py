from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEMORY_BANK = ROOT / "memory-bank"
REQUIRED_FILES = [
    "projectbrief.md",
    "productContext.md",
    "techContext.md",
    "activeContext.md",
    "progress.md",
    "pmbotSafety.md",
    "pmbotMarkets.md",
    "codexAutomation.md",
]
MARKET_IDS = ["563650", "597964", "598936", "691547", "692258", "573656"]


def test_memory_bank_required_files_exist() -> None:
    for filename in REQUIRED_FILES:
        assert (MEMORY_BANK / filename).exists()


def test_active_context_contains_latest_head_and_milestone() -> None:
    text = (MEMORY_BANK / "activeContext.md").read_text(encoding="utf-8")
    assert "8e6f19f2fcff5165b8505e3788be148c4b544b83" in text
    assert "ORCH-CODEX-AUTOMATION-027-ACTUAL-APP-SERVER-SESSION-DRY-RUN" in text
    assert "ORCH-CODEX-AUTOMATION-028-AGENTS-MD-SUBAGENTS-MEMORY-BANK-AND-MAINTENANCE" in text


def test_pmbot_markets_are_all_unresolved() -> None:
    text = (MEMORY_BANK / "pmbotMarkets.md").read_text(encoding="utf-8")
    assert "feedback_ready_count = 0" in text
    for market_id in MARKET_IDS:
        assert market_id in text
    assert text.count("unresolved") >= len(MARKET_IDS)
