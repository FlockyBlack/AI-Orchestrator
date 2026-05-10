from __future__ import annotations

from pathlib import Path

from pm_bot.practical.practical_safety_scan import run_practical_safety_scan

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/night_002")
UNSAFE_FIXTURE = Path("pm_bot/tests/fixtures/practical_market_queue_batch/unsafe_trading_instruction_fixture.md")


def test_safety_scan_passes_clean_artifacts(tmp_path: Path) -> None:
    report = run_practical_safety_scan(
        artifact_dirs=[ARTIFACT_DIR],
        out_json_path=tmp_path / "scan.json",
        out_md_path=tmp_path / "scan.md",
    )

    assert report["safety_ok"] is True
    assert report["issue_count"] == 0


def test_safety_scan_detects_intentionally_unsafe_fixture(tmp_path: Path) -> None:
    report = run_practical_safety_scan(
        artifact_paths=[UNSAFE_FIXTURE],
        out_json_path=tmp_path / "scan.json",
        out_md_path=tmp_path / "scan.md",
    )

    assert report["safety_ok"] is False
    assert report["issues"][0]["issue_type"] == "actionable_trading_wording"
