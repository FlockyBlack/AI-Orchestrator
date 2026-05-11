from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_AGENT = ROOT / ".codex-agent"


def test_phase_card_contains_all_phases() -> None:
    text = (CODEX_AGENT / "phase-card.md").read_text(encoding="utf-8")
    for phase in ["DISCOVERY", "PLANNING", "APPROVAL", "EXECUTION", "VERIFICATION", "HANDOFF"]:
        assert phase in text
    assert "allowed actions" in text.lower()
    assert "forbidden actions" in text.lower()
    assert "required outputs" in text.lower()


def test_approval_snapshot_is_valid_json() -> None:
    payload = json.loads((CODEX_AGENT / "approval-snapshot.json").read_text(encoding="utf-8"))
    assert payload["approved_scope"] == "ORCH-CODEX-AUTOMATION-028 only"
    assert payload["current_head"] == "8e6f19f2fcff5165b8505e3788be148c4b544b83"
    assert payload["safety_ok"] is True
    assert "AGENTS.md" in payload["allowed_paths"]
