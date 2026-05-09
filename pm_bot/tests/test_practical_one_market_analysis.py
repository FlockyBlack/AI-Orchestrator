from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from pm_bot.practical.one_market_analysis import (
    INPUT_CONTRACT_VERSION,
    PAPER_HYPOTHESIS_SAFETY_LABEL,
    RESULT_CONTRACT_VERSION,
    OneMarketAnalysisError,
    build_one_market_analysis_result,
    load_one_market_input,
    main,
    render_markdown_card,
    run_one_market_analysis,
    validate_one_market_input,
)

FIXTURE_DIR = Path("pm_bot/tests/fixtures/practical_one_market")
VALID_INPUT_PATH = FIXTURE_DIR / "one_market_input.valid.json"
STALE_INPUT_PATH = FIXTURE_DIR / "one_market_input.stale_sources.json"
CONTRADICTORY_INPUT_PATH = FIXTURE_DIR / "one_market_input.contradictory_sources.json"
MALFORMED_INPUT_PATH = FIXTURE_DIR / "one_market_input.malformed.json"
EXPECTED_SHAPE_PATH = FIXTURE_DIR / "expected_one_market_analysis_shape.valid.json"
SAMPLE_ANALYSIS_PATH = Path("pm_bot/practical/artifacts/one_market_analysis_sample_001.result.json")

SAFE_FLAGS = {
    "authenticated_endpoints_used": False,
    "live_network_used": False,
    "market_recommendation_generated": False,
    "openrouter_calls_performed": 0,
    "orders_or_trading_actions": False,
    "polymarket_api_calls_performed": 0,
    "probability_ev_edge_or_side_selection_generated": False,
    "runtime_or_dispatcher_changes": False,
    "wallet_or_private_key_access": False,
}
PAPER_HYPOTHESIS_FORBIDDEN_TOKENS = {
    "buy",
    "confidence",
    "edge",
    "enter",
    "ev",
    "exit",
    "hold",
    "probability",
    "sell",
}


def test_valid_one_market_input_produces_analysis_json_and_markdown(tmp_path: Path) -> None:
    out_json = tmp_path / "analysis.json"
    out_md = tmp_path / "analysis.md"

    result = run_one_market_analysis(
        input_path=VALID_INPUT_PATH,
        out_json_path=out_json,
        out_md_path=out_md,
    )

    written = json.loads(out_json.read_text(encoding="utf-8"))
    markdown = out_md.read_text(encoding="utf-8")
    expected_shape = json.loads(EXPECTED_SHAPE_PATH.read_text(encoding="utf-8"))

    assert result == written
    assert result["contract_version"] == RESULT_CONTRACT_VERSION
    assert result["analysis_mode"] == "local_one_market"
    assert set(expected_shape["required_top_level_keys"]).issubset(result)
    assert "# PMBOT One-Market Analysis Card" in markdown
    assert "Paper-only hypothesis for tracking" in markdown
    assert "Live network used: false." in markdown


def test_valid_input_contract_is_explicit_and_validates() -> None:
    payload = load_one_market_input(VALID_INPUT_PATH)
    validation = validate_one_market_input(payload)

    assert payload["contract_version"] == INPUT_CONTRACT_VERSION
    assert validation.valid is True
    assert validation.errors == ()


def test_sources_used_and_source_attribution_are_populated() -> None:
    result = build_one_market_analysis_result(load_one_market_input(VALID_INPUT_PATH))

    assert len(result["sources_used"]) == 2
    assert len(result["sources_not_used"]) == 1
    assert len(result["source_attribution"]) == 3
    assert {row["source_id"] for row in result["sources_used"]} == {
        "synthetic_city_agenda",
        "synthetic_local_article",
    }
    assert all("evidence_summary" in row for row in result["source_attribution"])


def test_stale_sources_are_detected() -> None:
    result = build_one_market_analysis_result(load_one_market_input(STALE_INPUT_PATH))

    assert result["evidence_status"]["stale_source_count"] == 1
    assert result["staleness_notes"] == [
        {
            "freshness_status": "stale",
            "note": "Source freshness needs operator review before reuse.",
            "source_id": "synthetic_old_city_agenda",
            "source_name": "Synthetic Old City Agenda",
        }
    ]


def test_contradictory_sources_are_detected() -> None:
    result = build_one_market_analysis_result(load_one_market_input(CONTRADICTORY_INPUT_PATH))

    assert result["evidence_status"]["contradiction_note_count"] == 1
    note = result["contradiction_notes"][0]
    assert note["claim_type"] == "permit_status"
    assert {item["claim_value"] for item in note["conflicting_values"]} == {
        "committee_forwarded",
        "committee_tabled",
    }


def test_malformed_input_fails_safely() -> None:
    payload = load_one_market_input(MALFORMED_INPUT_PATH)
    validation = validate_one_market_input(payload)

    assert validation.valid is False
    assert any("contract_version" in error for error in validation.errors)
    assert any("source_packets must be a non-empty list" in error for error in validation.errors)
    with pytest.raises(OneMarketAnalysisError):
        build_one_market_analysis_result(payload)


def test_analysis_result_safety_flags_are_safe() -> None:
    result = build_one_market_analysis_result(load_one_market_input(VALID_INPUT_PATH))

    for field_name, expected_value in SAFE_FLAGS.items():
        assert result[field_name] == expected_value
    assert result["no_real_trade_decision"] is True
    assert result["paper_hypothesis_allowed"] is True


def test_paper_hypothesis_is_paper_only_and_non_executable() -> None:
    result = build_one_market_analysis_result(load_one_market_input(VALID_INPUT_PATH))

    assert result["paper_hypothesis_safety_label"] == PAPER_HYPOTHESIS_SAFETY_LABEL
    assert result["paper_hypothesis"]["safety_label"] == PAPER_HYPOTHESIS_SAFETY_LABEL
    assert result["paper_hypothesis"]["execution_boundary"].startswith("Paper-only review record.")
    assert _find_forbidden_tokens(result["paper_hypothesis"]) == []


def test_cli_writes_local_only_analysis_artifacts(tmp_path: Path) -> None:
    out_json = tmp_path / "cli-analysis.json"
    out_md = tmp_path / "cli-analysis.md"

    exit_code = main(
        [
            "--input",
            str(VALID_INPUT_PATH),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
        ]
    )

    assert exit_code == 0
    result = json.loads(out_json.read_text(encoding="utf-8"))
    assert result["generated_artifacts"]["analysis_result_json"] == str(out_json).replace("\\", "/")
    assert result["generated_artifacts"]["analysis_card_markdown"] == str(out_md).replace("\\", "/")
    assert "No real trade decision was produced." in out_md.read_text(encoding="utf-8")


def test_markdown_card_is_deterministic() -> None:
    result = build_one_market_analysis_result(load_one_market_input(VALID_INPUT_PATH))

    assert render_markdown_card(result) == render_markdown_card(result)


def test_generated_sample_analysis_artifact_json_is_valid() -> None:
    artifact = json.loads(SAMPLE_ANALYSIS_PATH.read_text(encoding="utf-8"))

    assert artifact["contract_version"] == RESULT_CONTRACT_VERSION
    assert artifact["live_network_used"] is False
    assert artifact["openrouter_calls_performed"] == 0
    assert artifact["polymarket_api_calls_performed"] == 0


def _find_forbidden_tokens(value: object, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_path = f"{path}.{key}"
            if _has_token(str(key)):
                hits.append(key_path)
            hits.extend(_find_forbidden_tokens(nested, key_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            hits.extend(_find_forbidden_tokens(nested, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_token(value):
        hits.append(path)
    return hits


def _has_token(value: str) -> bool:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & PAPER_HYPOTHESIS_FORBIDDEN_TOKENS)
