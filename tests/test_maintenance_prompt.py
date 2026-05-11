from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "agent_tasks" / "automations" / "codex_maintenance_prompt.md"


def test_maintenance_prompt_is_report_only() -> None:
    text = PROMPT.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "report-only" in lowered
    assert "do not delete automatically" in lowered
    assert "produce cleanup report only" in lowered
    assert '"automatic_deletion_performed": false' in text
    assert "remove-item" not in lowered
    assert "rm -rf" not in lowered
