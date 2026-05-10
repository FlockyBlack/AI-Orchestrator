from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.local_market_packet_import import normalize_local_market_packet, run_local_market_packet_import
from pm_bot.practical.one_market_analysis import INPUT_CONTRACT_VERSION

FIXTURE_DIR = Path("pm_bot/tests/fixtures/practical_market_queue_batch")


def test_seed_packet_normalizes_to_one_market_input() -> None:
    normalized = normalize_local_market_packet(FIXTURE_DIR / "seeds/weather.seed.json")

    assert normalized["contract_version"] == INPUT_CONTRACT_VERSION
    assert normalized["market_id"] == "synthetic-weather-rain-001"
    assert normalized["source_packets"]


def test_missing_evidence_is_preserved_not_invented() -> None:
    normalized = normalize_local_market_packet(FIXTURE_DIR / "seeds/generic.seed.json")

    assert "Actual certificate filing record" in normalized["missing_evidence"]
    assert "Clerk timestamp for the filing" in normalized["missing_evidence"]


def test_import_cli_shape_writes_json_and_markdown(tmp_path: Path) -> None:
    out_json = tmp_path / "import.json"
    out_md = tmp_path / "import.md"

    normalized = run_local_market_packet_import(
        input_path=FIXTURE_DIR / "seeds/crypto.seed.json",
        out_json_path=out_json,
        out_md_path=out_md,
    )

    assert json.loads(out_json.read_text(encoding="utf-8")) == normalized
    assert "Missing evidence" in out_md.read_text(encoding="utf-8")
