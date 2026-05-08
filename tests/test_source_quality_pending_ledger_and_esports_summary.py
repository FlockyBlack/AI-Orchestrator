import ast
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import source_quality_pending_ledger as runner  # noqa: E402


MODULE_PATH = ROOT / "pm_bot" / "llm" / "source_quality_pending_ledger.py"
MARKET_CLASS_TAXONOMY_PATH = "pm_bot/llm/market_class_pilot_taxonomy.v1.json"


def _copy_file(root, relative_path):
    source = ROOT / relative_path
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _prepare_root(root):
    for relative_path in runner.INPUT_JSON_PATHS:
        _copy_file(root, relative_path)
    _copy_file(root, MARKET_CLASS_TAXONOMY_PATH)


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_artifacts(tmp_path):
    _prepare_root(tmp_path)
    return runner.write_artifacts(tmp_path)


def _iter_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield key
            yield from _iter_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_keys(item)


def _all_output_text(root):
    for relative_path in runner.JSON_OUTPUT_PATHS:
        path = root / relative_path
        yield path, json.dumps(_load_json(path), indent=2, sort_keys=True)
    for relative_path in runner.MARKDOWN_OUTPUT_PATHS:
        path = root / relative_path
        yield path, path.read_text(encoding="utf-8")


def test_dry_run_does_not_write_pending_ledger_artifacts(tmp_path):
    _prepare_root(tmp_path)

    result = runner.build_dry_run(tmp_path)

    assert result["status"] == "dry_run_no_write"
    assert result["files_written"] == []
    for relative_path in runner.OUTPUT_PATHS:
        assert not (tmp_path / relative_path).exists()


def test_write_creates_source_quality_pending_ledger_entry_for_1987056(tmp_path):
    summary = _write_artifacts(tmp_path)

    assert summary["status"] == "completed_local"
    assert summary["market_id"] == "1987056"
    assert (tmp_path / runner.LEDGER_ENTRY_JSON_PATH).exists()
    assert (tmp_path / runner.LEDGER_ENTRY_MD_PATH).exists()


def test_pending_ledger_has_outcome_known_false(tmp_path):
    _write_artifacts(tmp_path)
    ledger = _load_json(tmp_path / runner.LEDGER_ENTRY_JSON_PATH)

    assert ledger["outcome_known"] is False
    assert ledger["outcome_resolution_status"] == "unresolved"


def test_pending_ledger_has_source_scoring_performed_false(tmp_path):
    _write_artifacts(tmp_path)
    ledger = _load_json(tmp_path / runner.LEDGER_ENTRY_JSON_PATH)

    assert ledger["source_scoring_performed"] is False


def test_pending_ledger_has_source_ranking_updated_false(tmp_path):
    _write_artifacts(tmp_path)
    ledger = _load_json(tmp_path / runner.LEDGER_ENTRY_JSON_PATH)

    assert ledger["source_ranking_updated"] is False


def test_pending_ledger_has_profit_or_pnl_used_for_scoring_false(tmp_path):
    _write_artifacts(tmp_path)
    ledger = _load_json(tmp_path / runner.LEDGER_ENTRY_JSON_PATH)

    assert ledger["profit_or_pnl_used_for_scoring"] is False
    assert ledger["profit_or_pnl_recorded"] is False


def test_pending_ledger_forbids_profit_pnl_roi_ev_edge_metrics(tmp_path):
    _write_artifacts(tmp_path)
    ledger = _load_json(tmp_path / runner.LEDGER_ENTRY_JSON_PATH)
    forbidden = set(ledger["forbidden_metrics"])

    assert "profit_only_score" in forbidden
    assert "PnL" in forbidden
    assert "ROI" in forbidden
    assert "EV" in forbidden
    assert "edge" in forbidden
    assert "betting confidence" in forbidden
    assert "side selection" in forbidden
    assert "trade recommendation" in forbidden
    assert "autonomous execution score" in forbidden


def test_pending_ledger_index_exists_and_has_at_least_one_pending_entry(tmp_path):
    _write_artifacts(tmp_path)
    index = _load_json(tmp_path / runner.LEDGER_INDEX_JSON_PATH)

    assert index["pending_ledger_entries_count"] >= 1
    assert index["source_scoring_pending_count"] >= 1
    assert index["markets"]


def test_source_scoring_ready_count_is_zero_while_outcome_unresolved(tmp_path):
    _write_artifacts(tmp_path)
    index = _load_json(tmp_path / runner.LEDGER_INDEX_JSON_PATH)

    assert index["source_scoring_ready_count"] == 0
    assert all(market["outcome_known"] is False for market in index["markets"])


def test_esports_contour_summary_exists_and_includes_009a_through_paperlive005(tmp_path):
    _write_artifacts(tmp_path)
    summary = _load_json(tmp_path / runner.CONTOUR_SUMMARY_JSON_PATH)
    completed_stage_ids = {stage["stage_id"] for stage in summary["stages_completed"]}

    assert (tmp_path / runner.CONTOUR_SUMMARY_MD_PATH).exists()
    assert {
        "009A",
        "009B",
        "009C",
        "PAPERLIVE-001",
        "PAPERLIVE-002",
        "PAPERLIVE-003",
        "PAPERLIVE-004",
        "PAPERLIVE-005",
    }.issubset(completed_stage_ids)


def test_esports_contour_summary_says_outcome_unresolved_and_not_final(tmp_path):
    _write_artifacts(tmp_path)
    summary = _load_json(tmp_path / runner.CONTOUR_SUMMARY_JSON_PATH)

    assert summary["outcome_checked"] is True
    assert summary["outcome_known"] is False
    assert summary["outcome_resolution_status"] == "unresolved"
    assert summary["final_outcome_resolved"] is False


def test_esports_contour_summary_says_ready_for_autonomous_trading_false(tmp_path):
    _write_artifacts(tmp_path)
    summary = _load_json(tmp_path / runner.CONTOUR_SUMMARY_JSON_PATH)

    assert summary["ready_for_autonomous_trading"] is False
    assert summary["blockers_before_autonomous_trading"]


def test_handoff_readiness_artifact_exists(tmp_path):
    _write_artifacts(tmp_path)
    handoff = _load_json(tmp_path / runner.HANDOFF_JSON_PATH)

    assert (tmp_path / runner.HANDOFF_MD_PATH).exists()
    assert handoff["esports_market_id"] == "1987056"
    assert handoff["source_quality_scoring_completed"] is False


def test_handoff_readiness_allows_weather_pilot_or_explains_blockers(tmp_path):
    _write_artifacts(tmp_path)
    handoff = _load_json(tmp_path / runner.HANDOFF_JSON_PATH)

    assert handoff["source_quality_scoring_required_before_weather"] is False
    if handoff["weather_pilot_allowed"]:
        assert handoff["recommended_next_weather_task"] == runner.NEXT_WEATHER_TASK
    else:
        assert handoff["blockers"]


def test_passive_workbench_surface_exists_without_queue_runtime_dispatcher_changes(tmp_path):
    _write_artifacts(tmp_path)
    surface = _load_json(tmp_path / runner.WORKBENCH_SURFACE_JSON_PATH)

    assert (tmp_path / runner.WORKBENCH_SURFACE_MD_PATH).exists()
    assert surface["contour_summary_available"] is True
    assert surface["source_quality_pending_ledger_available"] is True
    assert surface["handoff_readiness_available"] is True
    assert surface["queue_mutated"] is False
    assert surface["runtime_wiring_changed"] is False
    assert surface["trading_runtime_changed"] is False
    assert surface["dispatcher_changed"] is False
    assert surface["background_worker_created"] is False
    assert surface["browser_automation_used"] is False
    assert surface["canonical_packets_mutated"] is False


def test_roadmap_artifact_exists_and_does_not_claim_autonomous_trading_ready(tmp_path):
    _write_artifacts(tmp_path)
    roadmap = _load_json(tmp_path / runner.ROADMAP_JSON_PATH)

    assert (tmp_path / runner.ROADMAP_MD_PATH).exists()
    assert roadmap["next_weather_pilot_task"] == runner.NEXT_WEATHER_TASK
    assert roadmap["ready_for_autonomous_trading"] is False


def test_existing_paperlive005_state_preserved(tmp_path):
    _prepare_root(tmp_path)
    before_reconciliation = _load_json(tmp_path / runner.PAPERLIVE005_RECONCILIATION_PATH)
    before_quality = _load_json(
        tmp_path / runner.PAPERLIVE005_SOURCE_QUALITY_PENDING_UPDATE_PATH
    )

    runner.write_artifacts(tmp_path)

    after_reconciliation = _load_json(tmp_path / runner.PAPERLIVE005_RECONCILIATION_PATH)
    after_quality = _load_json(
        tmp_path / runner.PAPERLIVE005_SOURCE_QUALITY_PENDING_UPDATE_PATH
    )
    assert after_reconciliation == before_reconciliation
    assert after_quality == before_quality
    assert after_reconciliation["outcome_known"] is False
    assert after_reconciliation["source_alignment_review_performed"] is False
    assert after_reconciliation["source_quality_update_performed"] is False


def test_existing_source_counts_preserved(tmp_path):
    _write_artifacts(tmp_path)
    result = _load_json(tmp_path / runner.DOC_RESULT_JSON_PATH)

    assert result["real_ingested_template_count_preserved_or_after"] >= 2
    assert result["draft_ingested_template_count_preserved_or_after"] >= 2
    assert result["ready_ingested_template_count_after"] == 0
    assert result["future_live_002_allowed"] is False


def test_no_openrouter_api_network_wallet_order_runtime_dispatcher_queue_browser_behavior(
    tmp_path,
):
    _write_artifacts(tmp_path)
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib",
        "webbrowser",
        "selenium",
        "playwright",
        "subprocess",
        "os",
    }
    forbidden_call_names = {
        "urlopen",
        "request",
        "post",
        "put",
        "patch",
        "delete",
        "getenv",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Attribute):
            assert node.attr.lower() not in forbidden_call_names

    lowered_source = source.lower()
    assert ("openrouter" + "_api_key") not in lowered_source
    assert "api.openrouter" not in lowered_source
    assert "openrouter.ai" not in lowered_source
    assert ("author" + "ization") not in lowered_source
    assert ("bearer" + " ") not in lowered_source
    assert "os.environ" not in lowered_source
    assert "runtime/" not in lowered_source
    assert "dispatcher/" not in lowered_source
    assert "queue/" not in lowered_source

    for path, text in _all_output_text(tmp_path):
        lowered_text = text.lower()
        assert ("openrouter" + "_api_key") not in lowered_text, path
        assert ("begin" + " private key") not in lowered_text, path
        assert ("bearer" + " ") not in lowered_text, path
        assert "requests." not in lowered_text, path
        assert "httpx." not in lowered_text, path
        assert "urlopen" not in lowered_text, path
        assert "playwright" not in lowered_text, path
        assert "selenium" not in lowered_text, path
        if "authenticated endpoint" in lowered_text:
            assert (
                "no authenticated endpoint" in lowered_text
                or '"authenticated_endpoints_used": false' in lowered_text
            ), path
        if "queue" in lowered_text:
            assert "no_queue_authority" in lowered_text or "no queue" in lowered_text, path
        if "runtime" in lowered_text:
            assert (
                "no_runtime_authority" in lowered_text
                or "no runtime" in lowered_text
                or '"runtime_wiring_changed": false' in lowered_text
                or '"trading_runtime_changed": false' in lowered_text
            ), path


def test_no_decision_metric_or_recommendation_fields_outside_safety_keys(tmp_path):
    _write_artifacts(tmp_path)
    allowed_keys = {
        "no_probability_ev_edge_confidence_side_selection",
        "probability_ev_edge_confidence_generated",
        "side_selection_generated",
        "selected_side",
        "next_recommended_action",
        "recommended_next_weather_task",
        "recommended_if_operator_wants_to_finish_esports_first",
    }
    forbidden = {
        "probability",
        "ev",
        "edge",
        "confidence",
        "confidence_score",
        "probability_score",
        "ev_score",
        "edge_score",
        "side_selection",
        "recommended_side",
        "recommendation",
    }

    for relative_path in runner.JSON_OUTPUT_PATHS:
        keys = {key.lower() for key in _iter_keys(_load_json(tmp_path / relative_path))}
        assert forbidden.isdisjoint(keys - allowed_keys), relative_path


def test_no_forbidden_action_language_in_new_markdown_except_safety_context(tmp_path):
    _write_artifacts(tmp_path)
    forbidden_terms = [
        "probability",
        "EV",
        "edge",
        "confidence",
        "side selection",
        "buy",
        "sell",
        "hold",
        "enter",
        "exit",
        "recommendation",
    ]
    safety_markers = (
        "no ",
        "not ",
        "null",
        "false",
        "pending",
        "safety",
        "does not",
        "do not",
        "without",
        "_generated",
        "operator review",
        "forbidden",
        "planned",
        "passive",
        "unresolved",
        "not ready",
    )

    for relative_path in runner.MARKDOWN_OUTPUT_PATHS:
        path = tmp_path / relative_path
        for line in path.read_text(encoding="utf-8").splitlines():
            lowered = line.lower()
            for term in forbidden_terms:
                pattern = rf"\b{re.escape(term.lower())}\b"
                if re.search(pattern, lowered):
                    assert any(marker in lowered for marker in safety_markers), (
                        path,
                        line,
                    )


def test_summary_only_reports_written_artifacts(tmp_path):
    _write_artifacts(tmp_path)

    summary = runner.build_summary_only(tmp_path)

    assert summary["status"] == "summary_only"
    assert summary["source_quality_pending_ledger_entry_exists"] is True
    assert summary["source_quality_pending_ledger_index_exists"] is True
    assert summary["esports_contour_summary_exists"] is True
    assert summary["esports_to_weather_handoff_readiness_exists"] is True
    assert summary["passive_workbench_surface_exists"] is True
    assert summary["roadmap_exists"] is True
    assert summary["outcome_known"] is False
    assert summary["source_scoring_ready_count"] == 0
