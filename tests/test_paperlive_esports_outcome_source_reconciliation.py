import ast
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.paper_live import esports_outcome_source_reconciliation as runner  # noqa: E402


MODULE_PATH = (
    ROOT / "pm_bot" / "paper_live" / "esports_outcome_source_reconciliation.py"
)


def _copy_file(root, relative_path):
    source = ROOT / relative_path
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _prepare_root(root):
    for relative_path in runner.INPUT_JSON_PATHS:
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


def _write_artifacts(tmp_path):
    _prepare_root(tmp_path)
    return runner.write_artifacts(tmp_path)


def test_dry_run_does_not_write_reconciliation_artifacts(tmp_path):
    _prepare_root(tmp_path)

    result = runner.build_dry_run(tmp_path)

    assert result["status"] == "dry_run_no_write"
    assert result["files_written"] == []
    for relative_path in runner.OUTPUT_PATHS:
        assert not (tmp_path / relative_path).exists()


def test_write_creates_reconciliation_artifact_for_market_1987056(tmp_path):
    summary = _write_artifacts(tmp_path)

    assert summary["status"] == "completed_local"
    assert summary["market_id"] == "1987056"
    assert (tmp_path / runner.RECONCILIATION_JSON_PATH).exists()
    assert (tmp_path / runner.RECONCILIATION_MD_PATH).exists()


def test_reconciliation_reads_paperlive004_normalized_evidence(tmp_path):
    _write_artifacts(tmp_path)
    evidence = _load_json(tmp_path / runner.PAPERLIVE004_NORMALIZED_EVIDENCE_PATH)
    reconciliation = _load_json(tmp_path / runner.RECONCILIATION_JSON_PATH)
    normalized_summary = reconciliation["normalized_evidence_summary"]

    assert normalized_summary["outcome_evidence_status"] == evidence[
        "outcome_evidence_status"
    ]
    assert normalized_summary["outcome_known"] == evidence["outcome_known"]
    assert normalized_summary["outcome_resolution_status"] == evidence[
        "outcome_resolution_status"
    ]
    assert normalized_summary["result_source_name"] == evidence["result_source_name"]


def test_unresolved_outcome_keeps_safe_pending_reconciliation_status(tmp_path):
    _write_artifacts(tmp_path)
    reconciliation = _load_json(tmp_path / runner.RECONCILIATION_JSON_PATH)

    assert reconciliation["outcome_known"] is False
    assert reconciliation["outcome_resolution_status"] == "unresolved"
    assert reconciliation["reconciliation_status"] in {
        "pending_unresolved",
        "evidence_available_pending_review",
        "blocked_missing_outcome",
    }
    assert reconciliation["reconciliation_status"] == "pending_unresolved"


def test_unresolved_outcome_does_not_perform_source_alignment_or_quality_update(tmp_path):
    _write_artifacts(tmp_path)
    reconciliation = _load_json(tmp_path / runner.RECONCILIATION_JSON_PATH)
    summary = _load_json(tmp_path / runner.RUN_SUMMARY_JSON_PATH)

    assert reconciliation["source_alignment_review_performed"] is False
    assert reconciliation["source_quality_update_performed"] is False
    assert summary["source_alignment_reviews_performed_count"] == 0
    assert summary["source_quality_updates_performed_count"] == 0


def test_no_final_resolution_trade_side_stake_order_wallet_or_position(tmp_path):
    _write_artifacts(tmp_path)
    reconciliation = _load_json(tmp_path / runner.RECONCILIATION_JSON_PATH)
    summary = _load_json(tmp_path / runner.RUN_SUMMARY_JSON_PATH)

    assert reconciliation["final_outcome_resolved"] is False
    assert reconciliation["simulated_trade_created"] is False
    assert reconciliation["selected_side"] is None
    assert reconciliation["stake_amount"] is None
    assert reconciliation["orders_created"] is False
    assert reconciliation["wallet_or_private_key_accessed"] is False
    assert reconciliation["position_sizing_created"] is False
    assert summary["simulated_trades_created_count"] == 0
    assert summary["orders_created_count"] == 0
    assert summary["selected_side_count"] == 0
    assert summary["stake_amount_count"] == 0


def test_pending_source_alignment_review_exists_without_performing_review(tmp_path):
    _write_artifacts(tmp_path)
    pending = _load_json(tmp_path / runner.PENDING_ALIGNMENT_JSON_PATH)

    assert pending["review_status"] == "pending_outcome_resolution"
    assert pending["outcome_known"] is False
    assert pending["source_alignment_review_performed"] is False
    assert pending["operator_review_required"] is True
    assert pending["sources_to_review"]


def test_future_reconciliation_update_request_requires_explicit_network_approval(tmp_path):
    _write_artifacts(tmp_path)
    request = _load_json(tmp_path / runner.FUTURE_RECONCILIATION_REQUEST_JSON_PATH)

    assert request["request_status"] == "prepared_not_executed"
    assert request["outcome_known_now"] is False
    assert request["future_update_required"] is True
    assert request["future_network_required"] is True
    assert request["explicit_network_approval_required"] is True
    assert "wallet" in request["forbidden_future_actions"]
    assert "orders" in request["forbidden_future_actions"]


def test_source_quality_pending_update_does_not_score_or_rank_sources(tmp_path):
    _write_artifacts(tmp_path)
    update = _load_json(tmp_path / runner.SOURCE_QUALITY_PENDING_UPDATE_JSON_PATH)

    assert update["update_status"] == "pending_outcome_resolution"
    assert update["outcome_known"] is False
    assert update["source_scoring_performed"] is False
    assert update["source_ranking_updated"] is False
    assert update["profit_or_pnl_used"] is False


def test_source_quality_pending_update_forbids_profit_pnl_roi_ev_edge_metrics(tmp_path):
    _write_artifacts(tmp_path)
    update = _load_json(tmp_path / runner.SOURCE_QUALITY_PENDING_UPDATE_JSON_PATH)
    forbidden = set(update["forbidden_metrics"])

    assert "profit_only_score" in forbidden
    assert "PnL" in forbidden
    assert "ROI" in forbidden
    assert "EV" in forbidden
    assert "edge" in forbidden
    assert "betting confidence" in forbidden
    assert "side selection" in forbidden


def test_passive_workbench_surface_exists_without_queue_runtime_dispatcher_changes(tmp_path):
    _write_artifacts(tmp_path)
    surface = _load_json(tmp_path / runner.WORKBENCH_SURFACE_JSON_PATH)

    assert surface["reconciliation_artifact_available"] is True
    assert surface["future_reconciliation_update_request_available"] is True
    assert surface["operator_review_required"] is True
    assert surface["queue_mutated"] is False
    assert surface["runtime_wiring_changed"] is False
    assert surface["trading_runtime_changed"] is False
    assert surface["dispatcher_changed"] is False
    assert surface["background_worker_created"] is False
    assert surface["browser_automation_used"] is False
    assert surface["canonical_packets_mutated"] is False


def test_existing_paperlive004_state_preserved(tmp_path):
    _prepare_root(tmp_path)
    before = {
        path: _load_json(tmp_path / path)
        for path in [
            runner.PAPERLIVE004_RAW_FETCH_PATH,
            runner.PAPERLIVE004_NORMALIZED_EVIDENCE_PATH,
            runner.PAPERLIVE004_CALL_LEDGER_PATH,
            runner.PAPERLIVE004_RECONCILIATION_INPUT_PATH,
            runner.PAPERLIVE004_WORKBENCH_SURFACE_PATH,
        ]
    }

    runner.write_artifacts(tmp_path)

    after = {path: _load_json(tmp_path / path) for path in before}
    assert after == before


def test_existing_source_counts_preserved(tmp_path):
    _write_artifacts(tmp_path)
    summary = _load_json(tmp_path / runner.RUN_SUMMARY_JSON_PATH)

    assert summary["real_ingested_template_count_preserved_or_after"] >= 2
    assert summary["draft_ingested_template_count_preserved_or_after"] >= 2
    assert summary["ready_ingested_template_count_after"] == 0
    assert summary["future_live_002_allowed"] is False


def test_no_decision_metric_or_recommendation_fields_outside_safety_keys(tmp_path):
    _write_artifacts(tmp_path)
    allowed_keys = {
        "no_probability_ev_edge_confidence_side_selection",
        "probability_ev_edge_confidence_generated",
        "side_selection_generated",
        "selected_side",
        "next_recommended_action",
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
    assert "authorization" not in lowered_source
    assert ("bearer" + " ") not in lowered_source
    assert "os.environ" not in lowered_source

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
        "prepared only",
        "explicit network approval",
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
    assert summary["reconciliation_artifact_exists"] is True
    assert summary["pending_source_alignment_review_exists"] is True
    assert summary["future_reconciliation_update_request_exists"] is True
    assert summary["source_quality_pending_update_exists"] is True
    assert summary["passive_workbench_surface_exists"] is True
    assert summary["source_alignment_reviews_performed_count"] == 0
    assert summary["source_quality_updates_performed_count"] == 0
    assert summary["simulated_trades_created_count"] == 0
