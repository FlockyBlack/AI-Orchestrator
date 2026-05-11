from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_agents_md_exists_and_contains_safety_boundaries() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    required = [
        "no wallet/private keys/signing",
        "no real orders",
        "no trading endpoints",
        "no real-money actions",
        "no autonomous real trading",
        "no authenticated endpoints",
        "no browser automation",
        "no OpenRouter unless explicitly approved",
        "no Polymarket API unless explicitly approved",
        "no market recommendation as real trading advice",
        "no probability/EV/edge/confidence/side-selection as actionable real trading signal",
    ]
    for phrase in required:
        assert phrase in text


def test_agents_md_forbids_unsafe_git_staging() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "no git add ." in text
    assert "no git add -A" in text
    assert "no git add --all" in text
    assert "no force push" in text
    assert "selective staging only" in text
