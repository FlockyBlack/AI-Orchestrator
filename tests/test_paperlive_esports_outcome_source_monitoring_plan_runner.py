import ast
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.paper_live import esports_outcome_source_monitoring_plan_runner as runner  # noqa: E402


MODULE_PATH = (
    ROOT
    / "pm_bot"
    / "paper_live"
    / "esports_outcome_source_monitoring_plan_runner.py"
)


def _copy_file(root, relative_path):
    source = ROOT / relative_path
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _prepare_root(root):
    for relative_path in [
        runner.RAW_FETCH_PATH,
        runner.NORMALIZED_CANDIDATE_PATH,
        runner.SOURCE_CANDIDATE_PATH,
        runner.SOURCE_009A_CHECKLIST_JSON_PATH,
        runner.SOURCE_009A_CHECKLIST_MD_PATH,
        runner.CAPTURE_JSON_PATH,
        runner.CAPTURE_MD_PATH,
        runner.CAPTURE_OPERATOR_SURFACE_JSON_PATH,
        runner.CAPTURE_OPERATOR_SURFACE_MD_PATH,
        runner.SOURCE_QUALITY_CANDIDATE_JSON_PATH,
        runner.SOURCE_QUALITY_CANDIDATE_MD_PATH,
        runner.OPERATOR_SURFACE_JSON_PATH,
        runner.OPERATOR_SURFACE_MD_PATH,
        runner.OBSERVATION_PLAN_JSON_PATH,
        runner.OBSERVATION_PLAN_MD_PATH,
        runner.OUTCOME_CONTRACT_JSON_PATH,
        runner.OUTCOME_CONTRACT_MD_PATH,
        runner.SOURCE_QUALITY_FLOW_JSON_PATH,
        runner.SOURCE_QUALITY_FLOW_MD_PATH,
        runner.INGEST_RESULT_PATH,
        runner.INGEST_OVERLAY_PATH,
        runner.READINESS_REPORT_PATH,
        runner.READINESS_GATE_PATH,
        runner.PAPERLIVE001_LEDGER_JSON_PATH,
        runner.PAPERLIVE001_LEDGER_SUMMARY_JSON_PATH,
        runner.PAPERLIVE001_SOURCE_QUALITY_PENDING_JSON_PATH,
        runner.PAPERLIVE001_OUTCOME_PLACEHOLDER_JSON_PATH,
        runner.PAPERLIVE001_WORKBENCH_SURFACE_JSON_PATH,
    ]:
        _copy_file(root, relative_path)


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


def test_dry_run_does_not_write_monitoring_plan_artifacts(tmp_path):
    _prepare_root(tmp_path)

    result = runner.build_dry_run(tmp_path)

    assert result["status"] == "dry_run_no_write"
    assert result["files_written"] == []
    for relative_path in runner.OUTPUT_PATHS:
        assert not (tmp_path / relative_path).exists()


def test_write_creates_monitoring_plan_for_1987056(tmp_path):
    _prepare_root(tmp_path)

    summary = runner.write_artifacts(tmp_path)
    plan_path = tmp_path / runner.MONITORING_PLAN_JSON_PATH
    plan_md_path = tmp_path / runner.MONITORING_PLAN_MD_PATH
    plan = _load_json(plan_path)

    assert summary["status"] == "completed_local"
    assert plan_path.exists()
    assert plan_md_path.exists()
    assert plan["market_id"] == "1987056"
    assert plan["title_or_question"] == runner.MARKET_TITLE
    assert plan["monitoring_mode"] == "source_and_outcome_monitoring_plan_only"


def test_monitoring_plan_has_outcome_checked_false(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    plan = _load_json(tmp_path / runner.MONITORING_PLAN_JSON_PATH)

    assert plan["outcome_checked"] is False
    assert plan["outcome_resolution_status"] == "pending_not_checked"


def test_monitoring_plan_has_outcome_known_false(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    plan = _load_json(tmp_path / runner.MONITORING_PLAN_JSON_PATH)

    assert plan["outcome_known"] is False


def test_monitoring_plan_has_simulated_trade_created_false(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    plan = _load_json(tmp_path / runner.MONITORING_PLAN_JSON_PATH)

    assert plan["simulated_trade_created"] is False


def test_monitoring_plan_has_selected_side_null(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    plan = _load_json(tmp_path / runner.MONITORING_PLAN_JSON_PATH)

    assert plan["selected_side"] is None


def test_monitoring_plan_has_stake_amount_null(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    plan = _load_json(tmp_path / runner.MONITORING_PLAN_JSON_PATH)

    assert plan["stake_amount"] is None


def test_monitoring_plan_has_order_created_false(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    plan = _load_json(tmp_path / runner.MONITORING_PLAN_JSON_PATH)

    assert plan["order_created"] is False


def test_monitoring_plan_has_wallet_used_false(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    plan = _load_json(tmp_path / runner.MONITORING_PLAN_JSON_PATH)

    assert plan["wallet_used"] is False


def test_monitoring_plan_has_no_standalone_probability_or_side_selection_fields(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    plan = _load_json(tmp_path / runner.MONITORING_PLAN_JSON_PATH)
    keys = {key.lower() for key in _iter_keys(plan)}
    allowed_safety_keys = {
        "probability_ev_edge_confidence_generated",
        "side_selection_generated",
        "no_probability_ev_edge_confidence_side_selection",
        "selected_side",
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
    }

    assert forbidden.isdisjoint(keys - allowed_safety_keys)
    assert plan["probability_ev_edge_confidence_generated"] is False
    assert plan["side_selection_generated"] is False
    assert plan["market_action_guidance_generated"] is False


def test_source_monitoring_checklist_exists_and_has_required_sections(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    checklist_path = tmp_path / runner.CHECKLIST_JSON_PATH
    checklist = _load_json(checklist_path)
    section_ids = {section["section_id"] for section in checklist["sections"]}
    expected = {
        "polymarket_market_rules_source",
        "official_tournament_match_source",
        "team_player_identity_check",
        "match_format_check",
        "schedule_timezone_check",
        "cancellation_reschedule_forfeit_rule_check",
        "final_result_source_check",
        "outcome_reconciliation_readiness",
        "source_quality_update_readiness",
        "operator_review_required",
    }

    assert checklist_path.exists()
    assert expected == section_ids
    for section in checklist["sections"]:
        for item in section["items"]:
            assert item["current_status"] in {
                "known",
                "missing",
                "ambiguous",
                "pending_future_readonly_check",
            }
            assert item["requires_operator_review"] is True
            assert item["no_trading_authority"] is True


def test_future_readonly_outcome_check_request_exists_and_network_calls_zero(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    request_path = tmp_path / runner.FUTURE_OUTCOME_CHECK_JSON_PATH
    request = _load_json(request_path)

    assert request_path.exists()
    assert request["request_status"] == "prepared_not_executed"
    assert request["network_calls_performed"] == 0
    assert request["outcome_checked"] is False


def test_future_readonly_outcome_check_request_requires_explicit_network_approval(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    request = _load_json(tmp_path / runner.FUTURE_OUTCOME_CHECK_JSON_PATH)

    assert request["future_network_required"] is True
    assert request["explicit_network_approval_required"] is True
    assert "wallet" in request["forbidden_future_actions"]
    assert "orders" in request["forbidden_future_actions"]
    assert "market action recommendation" in request["forbidden_future_actions"]


def test_source_quality_update_plan_exists_and_does_not_score(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    plan_path = tmp_path / runner.SOURCE_QUALITY_UPDATE_PLAN_JSON_PATH
    plan = _load_json(plan_path)

    assert plan_path.exists()
    assert plan["update_status"] == "planned_not_performed"
    assert plan["outcome_known"] is False
    assert plan["source_scoring_performed"] is False
    assert plan["source_ranking_updated"] is False
    assert plan["profit_or_pnl_used"] is False


def test_source_quality_update_plan_forbids_profit_pnl_roi_ev_edge_metrics(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    plan = _load_json(tmp_path / runner.SOURCE_QUALITY_UPDATE_PLAN_JSON_PATH)
    forbidden_metrics = set(plan["forbidden_metrics"])

    assert "profit_only_score" in forbidden_metrics
    assert "PnL" in forbidden_metrics
    assert "ROI" in forbidden_metrics
    assert "EV" in forbidden_metrics
    assert "edge" in forbidden_metrics
    assert "betting confidence" in forbidden_metrics
    assert "side selection" in forbidden_metrics


def test_passive_workbench_surface_exists_without_queue_runtime_dispatcher_changes(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    surface_path = tmp_path / runner.WORKBENCH_SURFACE_JSON_PATH
    surface = _load_json(surface_path)

    assert surface_path.exists()
    assert surface["monitoring_plan_available"] is True
    assert surface["source_monitoring_checklist_available"] is True
    assert surface["future_outcome_check_request_available"] is True
    assert surface["source_quality_update_plan_available"] is True
    assert surface["queue_mutated"] is False
    assert surface["runtime_wiring_changed"] is False
    assert surface["dispatcher_changed"] is False
    assert surface["background_worker_created"] is False
    assert surface["browser_automation_used"] is False


def test_existing_paperlive001_state_preserved(tmp_path):
    _prepare_root(tmp_path)
    before = _load_json(tmp_path / runner.PAPERLIVE001_LEDGER_JSON_PATH)

    runner.write_artifacts(tmp_path)

    after = _load_json(tmp_path / runner.PAPERLIVE001_LEDGER_JSON_PATH)
    assert after == before
    assert after["simulated_trade_created"] is False
    assert after["selected_side"] is None
    assert after["stake_amount"] is None


def test_existing_source_009b_009c_counts_preserved(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    summary = _load_json(tmp_path / runner.RUN_SUMMARY_JSON_PATH)

    assert summary["real_ingested_template_count_preserved_or_after"] >= 2
    assert summary["draft_ingested_template_count_preserved_or_after"] >= 2
    assert summary["ready_ingested_template_count_after"] == 0
    assert summary["future_live_002_allowed"] is False


def test_no_openrouter_api_network_wallet_order_runtime_dispatcher_queue_browser_behavior(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

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

    lowered = source.lower()
    assert ("openrouter" + "_api_key") not in lowered
    assert "api.openrouter" not in lowered
    assert "openrouter.ai" not in lowered
    assert "authorization" not in lowered
    assert ("bearer" + " ") not in lowered
    assert "os.environ" not in lowered

    for path, text in _all_output_text(tmp_path):
        lowered_text = text.lower()
        assert ("openrouter" + "_api_key") not in lowered_text, path
        assert ("begin" + " private key") not in lowered_text, path
        assert ("bearer" + " ") not in lowered_text, path
        if "authenticated endpoint" in lowered_text:
            assert "no authenticated endpoint" in lowered_text, path
        if "queue" in lowered_text:
            assert "no_queue_authority" in lowered_text or "no queue" in lowered_text, path
        if "runtime" in lowered_text:
            assert "no_runtime_authority" in lowered_text or "no runtime" in lowered_text, path
        assert "requests." not in lowered_text, path
        assert "httpx." not in lowered_text, path
        assert "urlopen" not in lowered_text, path
        assert "playwright" not in lowered_text, path
        assert "selenium" not in lowered_text, path


def test_no_forbidden_action_language_in_new_markdown_except_safety_context(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

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


def test_run_summary_counts_and_docs_result_match_no_trade_contract(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    summary = _load_json(tmp_path / runner.RUN_SUMMARY_JSON_PATH)
    result = _load_json(tmp_path / runner.DOC_RESULT_JSON_PATH)

    assert summary["monitoring_plans_created_count"] == 1
    assert summary["source_monitoring_checklists_created_count"] == 1
    assert summary["future_outcome_check_requests_created_count"] == 1
    assert summary["source_quality_update_plans_created_count"] == 1
    assert summary["outcome_checks_performed_count"] == 0
    assert summary["simulated_trades_created_count"] == 0
    assert summary["orders_created_count"] == 0
    assert summary["selected_side_count"] == 0
    assert summary["stake_amount_count"] == 0
    assert summary["source_scoring_updates_performed_count"] == 0
    assert result["monitoring_plan_created"] is True
    assert result["source_monitoring_checklist_created"] is True
    assert result["future_readonly_outcome_check_request_created"] is True
    assert result["source_quality_update_plan_created"] is True
    assert result["passive_workbench_surface_created"] is True
    assert result["outcome_checked"] is False
    assert result["outcome_known"] is False


def test_summary_only_reports_written_artifacts_without_writing_more(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    summary = runner.build_summary_only(tmp_path)

    assert summary["status"] == "summary_only"
    assert summary["monitoring_plan_exists"] is True
    assert summary["source_monitoring_checklist_exists"] is True
    assert summary["future_outcome_check_request_exists"] is True
    assert summary["source_quality_update_plan_exists"] is True
    assert summary["passive_workbench_surface_exists"] is True
    assert summary["outcome_checks_performed_count"] == 0
    assert summary["simulated_trades_created_count"] == 0
    assert summary["orders_created_count"] == 0
    assert summary["selected_side_count"] == 0
    assert summary["stake_amount_count"] == 0
