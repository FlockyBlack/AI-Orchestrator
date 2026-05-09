from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.one_market_analysis import build_one_market_analysis_result, load_one_market_input
from pm_bot.practical.paper_feedback import build_paper_feedback_result, load_outcome_record
from pm_bot.practical.source_learning import (
    LEDGER_CONTRACT_VERSION,
    build_source_learning_ledger,
    main,
    render_source_learning_markdown,
    run_source_learning,
)

FIXTURE_DIR = Path("pm_bot/tests/fixtures/practical_one_market")
VALID_INPUT_PATH = FIXTURE_DIR / "one_market_input.valid.json"
ALIGNED_OUTCOME_PATH = FIXTURE_DIR / "one_market_outcome_record.resolved_aligned.json"
MISSING_EVIDENCE_OUTCOME_PATH = FIXTURE_DIR / "one_market_outcome_record.resolved_missed_due_to_missing_evidence.json"
EXPECTED_SHAPE_PATH = FIXTURE_DIR / "expected_source_learning_ledger_shape.valid.json"
SAMPLE_LEDGER_PATH = Path("pm_bot/practical/artifacts/source_learning_ledger_sample_001.result.json")


def test_source_learning_ledger_aggregates_source_usefulness_labels() -> None:
    ledger = build_source_learning_ledger([_feedback(ALIGNED_OUTCOME_PATH), _feedback(MISSING_EVIDENCE_OUTCOME_PATH)])

    assert ledger["contract_version"] == LEDGER_CONTRACT_VERSION
    assert ledger["source_usefulness_summary"] == {
        "insufficient": 2,
        "unused": 1,
    }
    assert {record["usefulness_label"] for record in ledger["source_records"]} == {
        "insufficient",
        "unused",
    }
    assert ledger["no_autonomous_training_performed"] is True
    assert ledger["no_real_trade_decision"] is True


def test_source_learning_ledger_shape_is_explicit() -> None:
    ledger = build_source_learning_ledger([_feedback(ALIGNED_OUTCOME_PATH)])
    expected_shape = json.loads(EXPECTED_SHAPE_PATH.read_text(encoding="utf-8"))

    assert set(expected_shape["required_top_level_keys"]).issubset(ledger)
    assert ledger["source_usefulness_summary"] == {
        "unused": 1,
        "useful": 2,
    }


def test_source_learning_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    feedback_path = tmp_path / "feedback.json"
    ledger_path = tmp_path / "ledger.json"
    ledger_md_path = tmp_path / "ledger.md"
    feedback_path.write_text(json.dumps(_feedback(ALIGNED_OUTCOME_PATH), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    exit_code = main(
        [
            "--feedback",
            str(feedback_path),
            "--out-json",
            str(ledger_path),
            "--out-md",
            str(ledger_md_path),
        ]
    )

    assert exit_code == 0
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    markdown = ledger_md_path.read_text(encoding="utf-8")
    assert ledger["contract_version"] == LEDGER_CONTRACT_VERSION
    assert ledger["no_autonomous_training_performed"] is True
    assert "# PMBOT Source Learning Ledger" in markdown
    assert "No autonomous training was performed." in markdown


def test_run_source_learning_accepts_multiple_feedback_files(tmp_path: Path) -> None:
    feedback_path_1 = tmp_path / "feedback-1.json"
    feedback_path_2 = tmp_path / "feedback-2.json"
    ledger_path = tmp_path / "ledger.json"
    ledger_md_path = tmp_path / "ledger.md"
    feedback_path_1.write_text(json.dumps(_feedback(ALIGNED_OUTCOME_PATH), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    feedback_path_2.write_text(
        json.dumps(_feedback(MISSING_EVIDENCE_OUTCOME_PATH), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    ledger = run_source_learning(
        feedback_paths=[feedback_path_1, feedback_path_2],
        out_json_path=ledger_path,
        out_md_path=ledger_md_path,
    )

    assert json.loads(ledger_path.read_text(encoding="utf-8")) == ledger
    assert len(ledger["input_feedback_ids"]) == 2
    assert ledger["generated_artifacts"]["source_learning_ledger_json"] == str(ledger_path).replace("\\", "/")
    assert ledger["generated_artifacts"]["source_learning_ledger_markdown"] == str(ledger_md_path).replace("\\", "/")


def test_source_learning_markdown_is_deterministic() -> None:
    ledger = build_source_learning_ledger([_feedback(ALIGNED_OUTCOME_PATH)])

    assert render_source_learning_markdown(ledger) == render_source_learning_markdown(ledger)


def test_generated_sample_source_learning_artifact_json_is_valid() -> None:
    artifact = json.loads(SAMPLE_LEDGER_PATH.read_text(encoding="utf-8"))

    assert artifact["contract_version"] == LEDGER_CONTRACT_VERSION
    assert artifact["no_autonomous_training_performed"] is True
    assert artifact["no_real_trade_decision"] is True


def _feedback(outcome_path: Path) -> dict:
    analysis = build_one_market_analysis_result(load_one_market_input(VALID_INPUT_PATH))
    return build_paper_feedback_result(analysis, load_outcome_record(outcome_path))
