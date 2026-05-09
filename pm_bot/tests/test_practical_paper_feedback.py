from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.one_market_analysis import build_one_market_analysis_result, load_one_market_input
from pm_bot.practical.paper_feedback import (
    FEEDBACK_RESULT_CONTRACT_VERSION,
    build_paper_feedback_result,
    load_outcome_record,
    main,
    render_feedback_markdown,
    run_paper_feedback,
)

FIXTURE_DIR = Path("pm_bot/tests/fixtures/practical_one_market")
VALID_INPUT_PATH = FIXTURE_DIR / "one_market_input.valid.json"
UNRESOLVED_OUTCOME_PATH = FIXTURE_DIR / "one_market_outcome_record.unresolved.json"
ALIGNED_OUTCOME_PATH = FIXTURE_DIR / "one_market_outcome_record.resolved_aligned.json"
MISSING_EVIDENCE_OUTCOME_PATH = FIXTURE_DIR / "one_market_outcome_record.resolved_missed_due_to_missing_evidence.json"
EXPECTED_SHAPE_PATH = FIXTURE_DIR / "expected_paper_feedback_shape.valid.json"
SAMPLE_FEEDBACK_PATH = Path("pm_bot/practical/artifacts/one_market_feedback_sample_001.result.json")


def test_feedback_can_be_generated_from_unresolved_outcome_record() -> None:
    analysis = _analysis()
    feedback = build_paper_feedback_result(analysis, load_outcome_record(UNRESOLVED_OUTCOME_PATH))

    assert feedback["contract_version"] == FEEDBACK_RESULT_CONTRACT_VERSION
    assert feedback["outcome_status"] == "unresolved"
    assert feedback["analysis_quality_label"] == "unresolved"
    assert feedback["paper_hypothesis_review"]["review_status"] == "outcome_pending"
    assert feedback["no_real_trade_decision"] is True


def test_feedback_can_be_generated_from_resolved_aligned_outcome_record() -> None:
    feedback = build_paper_feedback_result(_analysis(), load_outcome_record(ALIGNED_OUTCOME_PATH))

    assert feedback["analysis_quality_label"] == "useful"
    assert feedback["paper_hypothesis_review"]["review_status"] == "reviewed"
    assert {row["usefulness_label"] for row in feedback["source_contribution_review"]} == {
        "unused",
        "useful",
    }


def test_feedback_records_wrong_due_to_missing_evidence_case() -> None:
    feedback = build_paper_feedback_result(_analysis(), load_outcome_record(MISSING_EVIDENCE_OUTCOME_PATH))

    assert feedback["analysis_quality_label"] == "wrong_due_to_missing_evidence"
    assert any("Missing evidence was material" in item for item in feedback["missing_evidence_lessons"])
    assert {row["usefulness_label"] for row in feedback["source_contribution_review"]} == {
        "insufficient",
        "unused",
    }


def test_feedback_shape_and_safety_fields_are_safe() -> None:
    feedback = build_paper_feedback_result(_analysis(), load_outcome_record(ALIGNED_OUTCOME_PATH))
    expected_shape = json.loads(EXPECTED_SHAPE_PATH.read_text(encoding="utf-8"))

    assert set(expected_shape["required_top_level_keys"]).issubset(feedback)
    assert feedback["orders_or_trading_actions"] is False
    assert feedback["wallet_or_private_key_access"] is False
    assert feedback["no_real_trade_decision"] is True


def test_feedback_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    analysis_path = tmp_path / "analysis.json"
    feedback_path = tmp_path / "feedback.json"
    feedback_md_path = tmp_path / "feedback.md"
    analysis_path.write_text(json.dumps(_analysis(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    exit_code = main(
        [
            "--analysis",
            str(analysis_path),
            "--outcome",
            str(ALIGNED_OUTCOME_PATH),
            "--out-json",
            str(feedback_path),
            "--out-md",
            str(feedback_md_path),
        ]
    )

    assert exit_code == 0
    feedback = json.loads(feedback_path.read_text(encoding="utf-8"))
    markdown = feedback_md_path.read_text(encoding="utf-8")
    assert feedback["contract_version"] == FEEDBACK_RESULT_CONTRACT_VERSION
    assert "# PMBOT One-Market Paper Feedback" in markdown
    assert "Orders or trading actions: false." in markdown


def test_run_paper_feedback_writes_local_artifacts(tmp_path: Path) -> None:
    analysis_path = tmp_path / "analysis.json"
    feedback_path = tmp_path / "feedback.json"
    feedback_md_path = tmp_path / "feedback.md"
    analysis_path.write_text(json.dumps(_analysis(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = run_paper_feedback(
        analysis_path=analysis_path,
        outcome_path=ALIGNED_OUTCOME_PATH,
        out_json_path=feedback_path,
        out_md_path=feedback_md_path,
    )

    assert json.loads(feedback_path.read_text(encoding="utf-8")) == result
    assert result["generated_artifacts"]["feedback_result_json"] == str(feedback_path).replace("\\", "/")
    assert result["generated_artifacts"]["feedback_markdown"] == str(feedback_md_path).replace("\\", "/")


def test_feedback_markdown_is_deterministic() -> None:
    feedback = build_paper_feedback_result(_analysis(), load_outcome_record(ALIGNED_OUTCOME_PATH))

    assert render_feedback_markdown(feedback) == render_feedback_markdown(feedback)


def test_generated_sample_feedback_artifact_json_is_valid() -> None:
    artifact = json.loads(SAMPLE_FEEDBACK_PATH.read_text(encoding="utf-8"))

    assert artifact["contract_version"] == FEEDBACK_RESULT_CONTRACT_VERSION
    assert artifact["no_real_trade_decision"] is True
    assert artifact["orders_or_trading_actions"] is False
    assert artifact["wallet_or_private_key_access"] is False


def _analysis() -> dict:
    return build_one_market_analysis_result(load_one_market_input(VALID_INPUT_PATH))
