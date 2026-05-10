from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.active_paper_hypotheses import build_active_paper_hypotheses
from pm_bot.practical.local_market_packet_import import run_local_market_packet_import
from pm_bot.practical.market_queue import summarize_market_queue
from pm_bot.practical.one_market_analysis import run_one_market_analysis
from pm_bot.practical.operator_console import build_operator_console
from pm_bot.practical.outcome_check_queue import build_outcome_check_queue
from pm_bot.practical.paper_feedback import run_paper_feedback
from pm_bot.practical.practical_io import write_json
from pm_bot.practical.practical_safety_scan import run_practical_safety_scan
from pm_bot.practical.source_learning_batch import run_source_learning_batch
from pm_bot.practical.source_scorecard import run_source_scorecard

FIXTURE_DIR = Path("pm_bot/tests/fixtures/practical_market_queue_batch")


def test_practical_workflow_e2e(tmp_path: Path) -> None:
    input_json = tmp_path / "weather.input.json"
    import_md = tmp_path / "weather.import.md"
    analysis_json = tmp_path / "weather.analysis.json"
    analysis_md = tmp_path / "weather.analysis.md"
    feedback_json = tmp_path / "weather.feedback.json"
    feedback_md = tmp_path / "weather.feedback.md"
    ledger_json = tmp_path / "ledger.json"
    ledger_md = tmp_path / "ledger.md"
    scorecard_json = tmp_path / "scorecard.json"
    scorecard_md = tmp_path / "scorecard.md"

    normalized = run_local_market_packet_import(
        input_path=FIXTURE_DIR / "seeds/weather.seed.json",
        out_json_path=input_json,
        out_md_path=import_md,
    )
    analysis = run_one_market_analysis(input_path=input_json, out_json_path=analysis_json, out_md_path=analysis_md)
    queue_path = tmp_path / "queue.json"
    queue = {
        "contract_version": "pmbot_market_queue.v1",
        "created_at": "2026-05-10T00:00:00Z",
        "items": [
            {
                "queue_item_id": "e2e-weather-001",
                "market_id": normalized["market_id"],
                "market_title": normalized["market_title"],
                "market_type": normalized["market_type"],
                "local_input_path": str(input_json).replace("\\", "/"),
                "status": "feedback_ready",
                "created_at": "2026-05-10T00:00:00Z",
                "updated_at": "2026-05-10T00:00:00Z",
                "analysis_result_path": str(analysis_json).replace("\\", "/"),
                "analysis_markdown_path": str(analysis_md).replace("\\", "/"),
                "paper_hypothesis_id": analysis["paper_hypothesis"]["hypothesis_id"],
                "outcome_record_path": str(FIXTURE_DIR / "outcomes/weather.resolved.json").replace("\\", "/"),
                "feedback_result_path": "",
                "source_learning_ledger_path": "",
                "blockers": [],
                "next_operator_action": "",
            }
        ],
    }
    write_json(queue_path, queue)

    queue_summary = summarize_market_queue(queue_path)
    active = build_active_paper_hypotheses(queue_path)
    outcome_queue = build_outcome_check_queue(queue_path)
    feedback = run_paper_feedback(
        analysis_path=analysis_json,
        outcome_path=FIXTURE_DIR / "outcomes/weather.resolved.json",
        out_json_path=feedback_json,
        out_md_path=feedback_md,
    )
    ledger = run_source_learning_batch(feedback_paths=[feedback_json], out_json_path=ledger_json, out_md_path=ledger_md)
    scorecard = run_source_scorecard(ledger_path=str(ledger_json), out_json_path=str(scorecard_json), out_md_path=str(scorecard_md))

    queue["items"][0]["feedback_result_path"] = str(feedback_json).replace("\\", "/")
    queue["items"][0]["source_learning_ledger_path"] = str(ledger_json).replace("\\", "/")
    queue["items"][0]["status"] = "feedback_complete"
    write_json(queue_path, queue)
    console = build_operator_console(queue_path)
    safety = run_practical_safety_scan(
        artifact_paths=[analysis_json, analysis_md, feedback_json, feedback_md, ledger_json, ledger_md, scorecard_json, scorecard_md],
        out_json_path=tmp_path / "scan.json",
        out_md_path=tmp_path / "scan.md",
    )

    assert queue_summary["status_counts"]["feedback_ready"] == 1
    assert active["feedback_pending_count"] == 1
    assert outcome_queue["status_counts"]["resolved"] == 1
    assert feedback["analysis_quality_label"] == "useful"
    assert ledger["source_usefulness_summary"]["useful"] == 2
    assert scorecard["source_count"] == 2
    assert console["feedback_complete_count"] == 1
    assert safety["safety_ok"] is True
    assert json.loads((tmp_path / "scan.json").read_text(encoding="utf-8"))["issue_count"] == 0
