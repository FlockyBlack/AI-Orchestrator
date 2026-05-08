import ast
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.paper_live import weather_observation_ledger_first_run as first_run  # noqa: E402


MODULE_PATH = (
    ROOT / "pm_bot" / "paper_live" / "weather_observation_ledger_first_run.py"
)

JSON_OUTPUT_PATHS = [
    first_run.LEDGER_ENTRY_JSON_PATH,
    first_run.RUN_SUMMARY_JSON_PATH,
    first_run.SOURCE_QUALITY_PENDING_JSON_PATH,
    first_run.OUTCOME_PLACEHOLDER_JSON_PATH,
    first_run.WORKBENCH_SURFACE_JSON_PATH,
    first_run.DOC_RESULT_JSON_PATH,
]

MARKDOWN_OUTPUT_PATHS = [
    first_run.LEDGER_ENTRY_MD_PATH,
    first_run.RUN_SUMMARY_MD_PATH,
    first_run.SOURCE_QUALITY_PENDING_MD_PATH,
    first_run.OUTCOME_PLACEHOLDER_MD_PATH,
    first_run.WORKBENCH_SURFACE_MD_PATH,
    first_run.DOC_RESULT_MD_PATH,
]


def _copy_file(root, relative_path):
    source = ROOT / relative_path
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _prepare_root(root):
    for relative_path in [
        first_run.RAW_FETCH_PATH,
        first_run.NORMALIZED_CANDIDATE_PATH,
        first_run.SOURCE_CANDIDATE_PATH,
        first_run.CHECKLIST_JSON_PATH,
        first_run.CHECKLIST_MD_PATH,
        first_run.REFINEMENT_DIAGNOSTICS_PATH,
        first_run.SOURCE_QUALITY_010A2_JSON_PATH,
        first_run.CAPTURE_JSON_PATH,
        first_run.CAPTURE_MD_PATH,
        first_run.AUTOFILL_RESULT_PATH,
        first_run.AUTOFILL_SURFACE_JSON_PATH,
        first_run.AUTOFILL_SURFACE_MD_PATH,
        first_run.SOURCE_QUALITY_CANDIDATE_JSON_PATH,
        first_run.SOURCE_QUALITY_CANDIDATE_MD_PATH,
        first_run.OPERATOR_SURFACE_JSON_PATH,
        first_run.OPERATOR_SURFACE_MD_PATH,
        first_run.LEDGER_CONTRACT_JSON_PATH,
        first_run.OBSERVATION_PLAN_JSON_PATH,
        first_run.OBSERVATION_PLAN_MD_PATH,
        first_run.OUTCOME_CONTRACT_JSON_PATH,
        first_run.OUTCOME_CONTRACT_MD_PATH,
        first_run.SOURCE_QUALITY_FLOW_JSON_PATH,
        first_run.SOURCE_QUALITY_FLOW_MD_PATH,
        first_run.PREPARATION_SUMMARY_JSON_PATH,
        first_run.PREPARATION_SUMMARY_MD_PATH,
        first_run.PREPARATION_SURFACE_JSON_PATH,
        first_run.PREPARATION_SURFACE_MD_PATH,
        first_run.INGEST_RESULT_PATH,
        first_run.INGEST_OVERLAY_PATH,
        first_run.READINESS_REPORT_PATH,
        first_run.READINESS_GATE_PATH,
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
    for relative_path in JSON_OUTPUT_PATHS:
        path = root / relative_path
        yield path, json.dumps(_load_json(path), indent=2, sort_keys=True)
    for relative_path in MARKDOWN_OUTPUT_PATHS:
        path = root / relative_path
        yield path, path.read_text(encoding="utf-8")


def test_dry_run_does_not_write_observation_ledger_entry(tmp_path):
    _prepare_root(tmp_path)

    result = first_run.build_dry_run(tmp_path)

    assert result["status"] == "dry_run_no_write"
    assert result["files_written"] == []
    assert not (tmp_path / first_run.LEDGER_ENTRY_JSON_PATH).exists()
    assert not (tmp_path / first_run.LEDGER_ENTRY_MD_PATH).exists()


def test_write_creates_weather_observation_ledger_entry_for_693869(tmp_path):
    _prepare_root(tmp_path)

    summary = first_run.write_artifacts(tmp_path)
    ledger_path = tmp_path / first_run.LEDGER_ENTRY_JSON_PATH
    ledger_md_path = tmp_path / first_run.LEDGER_ENTRY_MD_PATH
    ledger = _load_json(ledger_path)

    assert summary["status"] == "completed_local"
    assert ledger_path.exists()
    assert ledger_md_path.exists()
    assert ledger["market_id"] == "693869"
    assert ledger["market_class"] == "weather"
    assert ledger["title_or_question"] == first_run.MARKET_TITLE


def test_ledger_entry_is_weather_observation_only_and_has_no_trade_fields_set(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    ledger = _load_json(tmp_path / first_run.LEDGER_ENTRY_JSON_PATH)

    assert ledger["observation_mode"] == "source_and_weather_outcome_tracking_only"
    assert ledger["paper_live_mode"] == "observation_only"
    assert ledger["simulated_trade_created"] is False
    assert ledger["selected_side"] is None
    assert ledger["stake_amount"] is None
    assert ledger["order_created"] is False
    assert ledger["wallet_used"] is False
    assert ledger["position_sizing_created"] is False
    assert ledger["outcome_checked"] is False
    assert ledger["outcome_known"] is False


def test_ledger_entry_has_required_weather_observation_sections(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    ledger = _load_json(tmp_path / first_run.LEDGER_ENTRY_JSON_PATH)
    monitored_ids = {item["fact_id"] for item in ledger["monitored_facts"]}
    source_roles = {item["source_role"] for item in ledger["required_sources"]}

    assert "exact_market_identity" in monitored_ids
    assert "arctic_sea_ice_extent_metric" in monitored_ids
    assert "minimum_extent_value" in monitored_ids
    assert "threshold_less_than_4_million_square_kilometers" in monitored_ids
    assert "unit_million_square_kilometers" in monitored_ids
    assert "relevant_summer_time_window" in monitored_ids
    assert "official_dataset_source_candidate" in monitored_ids
    assert "station_dataset_source_hierarchy" in monitored_ids
    assert "final_official_minimum_extent_value" in monitored_ids
    assert "polymarket_exact_rules_description_completeness" in monitored_ids
    assert "measurement_publication_timing" in monitored_ids
    assert "measurement_revision_risk" in monitored_ids
    assert "market_metadata_source" in source_roles
    assert "market_rules_source" in source_roles
    assert "official_weather_source_candidate" in source_roles
    assert "station_or_dataset_source_candidate" in source_roles
    assert "fallback_weather_source_candidate" in source_roles
    assert "local_capture_source" in source_roles
    assert "operator_review_surface" in source_roles
    assert ledger["missing_sources"]
    assert ledger["unresolved_questions"]
    assert ledger["source_capture_references"]
    assert ledger["operator_review_references"]
    assert ledger["weather_outcome_tracking_contract_reference"]
    assert ledger["source_quality_tracking_reference"]
    assert ledger["future_reconciliation_required"] is True


def test_ledger_entry_has_no_standalone_probability_or_side_selection_fields(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    ledger = _load_json(tmp_path / first_run.LEDGER_ENTRY_JSON_PATH)
    keys = {key.lower() for key in _iter_keys(ledger)}
    allowed_safety_keys = {
        "probability_ev_edge_confidence_generated",
        "no_probability_ev_edge_confidence_side_selection",
        "side_selection_generated",
        "market_action_guidance_generated",
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
    assert ledger["probability_ev_edge_confidence_generated"] is False
    assert ledger["side_selection_generated"] is False
    assert ledger["market_action_guidance_generated"] is False


def test_source_quality_pending_observation_exists_and_does_not_score(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    observation_path = tmp_path / first_run.SOURCE_QUALITY_PENDING_JSON_PATH
    observation = _load_json(observation_path)

    assert observation_path.exists()
    assert observation["source_quality_status"] == "pending_outcome_and_operator_review"
    assert observation["outcome_known"] is False
    assert observation["source_scoring_performed"] is False
    assert observation["source_ranking_updated"] is False
    assert observation["trading_profit_used_for_scoring"] is False
    assert observation["profit_or_pnl_recorded"] is False
    assert observation["operator_review_required"] is True
    assert observation["future_update_allowed_only_after_outcome_review"] is True


def test_source_quality_pending_observation_roles_are_allowed(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    observation = _load_json(tmp_path / first_run.SOURCE_QUALITY_PENDING_JSON_PATH)

    assert set(observation["source_roles_observed"]).issubset(
        first_run.ALLOWED_SOURCE_ROLES
    )
    assert "market_metadata_source" in observation["source_roles_observed"]
    assert "market_rules_source" in observation["source_roles_observed"]
    assert "official_weather_source_candidate" in observation["source_roles_observed"]
    assert "station_or_dataset_source_candidate" in observation["source_roles_observed"]
    assert "fallback_weather_source_candidate" in observation["source_roles_observed"]
    assert "local_capture_source" in observation["source_roles_observed"]
    assert "operator_review_surface" in observation["source_roles_observed"]
    assert "paper_live_observation_source" in observation["source_roles_observed"]


def test_outcome_reconciliation_placeholder_exists_and_outcome_unknown(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    placeholder_path = tmp_path / first_run.OUTCOME_PLACEHOLDER_JSON_PATH
    placeholder = _load_json(placeholder_path)

    assert placeholder_path.exists()
    assert placeholder["outcome_known"] is False
    assert placeholder["outcome_resolution_status"] == "pending"
    assert placeholder["outcome_source_required"] is True
    assert placeholder["official_weather_source_required"] is True
    assert placeholder["official_dataset_or_source_required"] is True
    assert placeholder["final_measurement_required"] is True
    assert placeholder["unit_required"] is True
    assert placeholder["time_window_required"] is True
    assert (
        placeholder["reconciliation_not_performed_reason"]
        == "outcome_not_checked_in_this_task"
    )
    assert placeholder["source_alignment_review_pending"] is True
    assert placeholder["source_quality_update_pending"] is True
    assert placeholder["no_market_action_guidance"] is True
    assert placeholder["no_trading_authority"] is True


def test_passive_workbench_surface_exists_without_queue_or_runtime_changes(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    surface_path = tmp_path / first_run.WORKBENCH_SURFACE_JSON_PATH
    surface = _load_json(surface_path)

    assert surface_path.exists()
    assert surface["observation_ledger_entry_available"] is True
    assert surface["source_quality_pending_observation_available"] is True
    assert surface["outcome_reconciliation_placeholder_available"] is True
    assert surface["operator_review_required"] is True
    assert surface["simulated_trade_created"] is False
    assert surface["selected_side"] is None
    assert surface["stake_amount"] is None
    assert surface["outcome_checked"] is False
    assert surface["outcome_known"] is False
    assert surface["queue_mutated"] is False
    assert surface["runtime_wiring_changed"] is False
    assert surface["dispatcher_changed"] is False
    assert surface["background_worker_created"] is False
    assert surface["browser_automation_used"] is False


def test_run_summary_preserves_source_010b_010c_counts(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    summary = _load_json(tmp_path / first_run.RUN_SUMMARY_JSON_PATH)

    assert summary["observation_entries_created_count"] == 1
    assert summary["simulated_trades_created_count"] == 0
    assert summary["orders_created_count"] == 0
    assert summary["selected_side_count"] == 0
    assert summary["stake_amount_count"] == 0
    assert summary["source_quality_pending_observations_created_count"] == 1
    assert summary["outcome_reconciliation_placeholders_created_count"] == 1
    assert summary["real_ingested_template_count_preserved_or_after"] >= 3
    assert summary["draft_ingested_template_count_preserved_or_after"] >= 3
    assert summary["ready_ingested_template_count_after"] == 0
    assert summary["future_live_002_allowed"] is False
    assert summary["ready_for_autonomous_trading"] is False


def test_no_openrouter_api_network_wallet_order_or_runtime_behavior_introduced(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

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
    assert "openrouter_api_key" not in lowered
    assert "api.openrouter" not in lowered
    assert "openrouter.ai" not in lowered
    assert "authorization" not in lowered
    assert "bearer " not in lowered
    assert "os.environ" not in lowered
    assert "wallet" not in lowered or "no_wallet" in lowered

    for path, text in _all_output_text(tmp_path):
        lowered_text = text.lower()
        assert "openrouter_api_key" not in lowered_text, path
        assert "begin private key" not in lowered_text, path
        assert "bearer " not in lowered_text, path
        if "authenticated endpoint" in lowered_text:
            assert "no authenticated endpoint" in lowered_text, path
        assert "requests." not in lowered_text, path
        assert "httpx." not in lowered_text, path
        assert "urlopen" not in lowered_text, path
        assert "playwright" not in lowered_text, path
        assert "selenium" not in lowered_text, path


def test_safety_counters_are_zero_and_authority_flags_are_false(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    payloads = [_load_json(tmp_path / path) for path in JSON_OUTPUT_PATHS]
    for payload in payloads:
        safety = payload.get("safety_summary", {})
        assert safety.get("openrouter_calls_performed") == 0
        assert safety.get("polymarket_api_calls_performed") == 0
        assert safety.get("external_network_calls_performed") == 0
        assert safety.get("network_calls_performed") == 0
        assert safety.get("wallet_or_private_key_accessed") is False
        assert safety.get("orders_created") in (0, False)
        assert safety.get("simulated_trade_created") is False
        assert safety.get("selected_side") is None
        assert safety.get("stake_amount") is None
        assert safety.get("outcome_checked") is False
        assert safety.get("outcome_known") is False
        assert safety.get("source_scoring_performed") is False
        assert safety.get("source_ranking_updated") is False
        assert safety.get("queue_state_mutated") is False
        assert safety.get("runtime_wiring_added") is False
        assert safety.get("dispatcher_changed") is False
        assert safety.get("background_workers_added") is False
        assert safety.get("browser_automation_used") is False
        assert safety.get("market_decisions_made") is False
        assert safety.get("canonical_packets_mutated") is False


def test_no_forbidden_source_quality_or_market_decision_keys_in_outputs(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    allowed_safety_keys = {
        "probability_ev_edge_confidence_generated",
        "no_probability_ev_edge_confidence_side_selection",
        "side_selection_generated",
        "market_action_guidance_generated",
        "selected_side",
        "stake_amount",
        "stake_amount_count",
        "profit_or_pnl_recorded",
        "trading_profit_used_for_scoring",
        "trading_profit_used_for_source_scoring",
    }
    forbidden_keys = {
        "profit_score",
        "betting_confidence",
        "edge",
        "ev",
        "recommendation",
        "side selection",
        "side_selection",
        "profitable_trade_count",
        "pnl",
        "roi",
        "recommended_side",
        "buy_score",
        "sell_score",
        "position_size",
    }

    for relative_path in JSON_OUTPUT_PATHS:
        payload = _load_json(tmp_path / relative_path)
        keys = {key.lower() for key in _iter_keys(payload)}
        assert forbidden_keys.isdisjoint(keys - allowed_safety_keys), relative_path


def test_forbidden_action_language_in_markdown_only_appears_in_safety_context(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    forbidden_terms = [
        "probability",
        "ev",
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
    )

    for relative_path in MARKDOWN_OUTPUT_PATHS:
        path = tmp_path / relative_path
        for line in path.read_text(encoding="utf-8").splitlines():
            lowered = line.lower()
            for term in forbidden_terms:
                if re.search(rf"\b{re.escape(term.lower())}\b", lowered):
                    assert any(marker in lowered for marker in safety_markers), (
                        path,
                        line,
                    )


def test_docs_result_matches_no_trade_contract(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    result = _load_json(tmp_path / first_run.DOC_RESULT_JSON_PATH)

    assert result["observation_ledger_entry_created"] is True
    assert result["source_quality_pending_observation_created"] is True
    assert result["outcome_reconciliation_placeholder_created"] is True
    assert result["passive_workbench_surface_created"] is True
    assert result["orders_created"] is False
    assert result["simulated_trade_created"] is False
    assert result["selected_side"] is None
    assert result["stake_amount"] is None
    assert result["position_sizing_created"] is False
    assert result["outcome_checked"] is False
    assert result["outcome_known"] is False
    assert result["profit_or_pnl_recorded"] is False
    assert result["source_scoring_performed"] is False
    assert result["source_ranking_updated"] is False
    assert result["ready_for_autonomous_trading"] is False


def test_summary_only_reports_written_artifacts_without_writing_more(tmp_path):
    _prepare_root(tmp_path)
    first_run.write_artifacts(tmp_path)

    summary = first_run.build_summary_only(tmp_path)

    assert summary["status"] == "summary_only"
    assert summary["observation_ledger_entry_exists"] is True
    assert summary["source_quality_pending_observation_exists"] is True
    assert summary["outcome_reconciliation_placeholder_exists"] is True
    assert summary["passive_workbench_surface_exists"] is True
    assert summary["simulated_trades_created_count"] == 0
    assert summary["orders_created_count"] == 0
    assert summary["selected_side_count"] == 0
    assert summary["stake_amount_count"] == 0
    assert summary["outcome_checked"] is False
    assert summary["outcome_known"] is False
    assert summary["ready_for_autonomous_trading"] is False
