import ast
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import export_post_capture_readiness as post_capture  # noqa: E402
from pm_bot.llm import ingest_manual_resolution_source_capture as ingest  # noqa: E402
from pm_bot.llm import manual_resolution_source_capture_validator as validator  # noqa: E402
from pm_bot.llm import weather_capture_autofill_from_readonly_candidate as autofill  # noqa: E402


MODULE_PATH = ROOT / "pm_bot" / "llm" / "weather_capture_autofill_from_readonly_candidate.py"
INGEST_RESULT = ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_ingest_result.v1.json"
READINESS_GATE = ROOT / "pm_bot" / "llm" / "post_capture_batch_readiness_gate.v1.json"
PAPERLIVE_006_RESULT = ROOT / "docs" / "PMBOT_PAPERLIVE_006_RESULT.json"


def _copy_file(root, relative_path):
    source = ROOT / relative_path
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _copy_010a2_inputs(root):
    for relative_path in [
        autofill.RAW_FETCH_PATH,
        autofill.NORMALIZED_CANDIDATE_PATH,
        autofill.SOURCE_CANDIDATE_PATH,
        autofill.CHECKLIST_JSON_PATH,
        autofill.CHECKLIST_MD_PATH,
        autofill.REFINEMENT_DIAGNOSTICS_PATH,
        autofill.SOURCE_QUALITY_010A2_PATH,
    ]:
        _copy_file(root, relative_path)


def _copy_validator_schema(root):
    _copy_file(root, "pm_bot/llm/manual_resolution_source_capture_schema.v1.json")


def _copy_existing_capture(root, market_id):
    for suffix in ("json", "md"):
        _copy_file(
            root,
            f"pm_bot/llm/manual_resolution_source_capture/{market_id}_resolution_source_capture.v1.{suffix}",
        )


def _write_readiness_before(root):
    path = (
        root
        / "pm_bot"
        / "llm"
        / "current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "aggregate": {
                    "updated_average_score": 0,
                    "updated_high_count": 0,
                    "updated_medium_count": 0,
                    "updated_low_count": 0,
                    "updated_blocked_count": 0,
                },
                "markets": [],
            },
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _iter_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield key
            yield from _iter_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_keys(item)


def _prepare_root(root):
    _copy_010a2_inputs(root)
    _copy_validator_schema(root)


def test_dry_run_does_not_write_capture_file(tmp_path):
    _prepare_root(tmp_path)

    result = autofill.build_autofill_result(tmp_path, dry_run=True, capture_written=False)

    assert result["status"] == "dry_run_no_write"
    assert result["capture_written"] is False
    assert not (tmp_path / autofill.TARGET_CAPTURE_JSON_PATH).exists()
    assert not (tmp_path / autofill.TARGET_CAPTURE_MD_PATH).exists()


def test_write_creates_693869_manual_capture_json_and_markdown(tmp_path):
    _prepare_root(tmp_path)

    result = autofill.write_autofill_artifacts(tmp_path)

    capture_json = tmp_path / autofill.TARGET_CAPTURE_JSON_PATH
    capture_md = tmp_path / autofill.TARGET_CAPTURE_MD_PATH
    assert result["capture_written"] is True
    assert capture_json.exists()
    assert capture_md.exists()
    capture = _load_json(capture_json)
    assert capture["market_id"] == "693869"
    assert capture["market_title_or_question"] == autofill.MARKET_TITLE


def test_created_capture_stays_draft_and_operator_review_only(tmp_path):
    _prepare_root(tmp_path)
    autofill.write_autofill_artifacts(tmp_path)

    capture = _load_json(tmp_path / autofill.TARGET_CAPTURE_JSON_PATH)

    assert capture["source_capture_status"] == "draft"
    assert capture["capture_status"] == "draft"
    assert capture["operator_review_required"] is True
    assert capture["operator_review_only"] is True
    assert capture["no_trading_authority"] is True
    assert capture["no_queue_authority"] is True
    assert capture["no_runtime_authority"] is True
    assert capture["no_wallet_or_order_authority"] is True


def test_created_capture_has_no_decision_or_scoring_fields(tmp_path):
    _prepare_root(tmp_path)
    autofill.write_autofill_artifacts(tmp_path)

    capture = _load_json(tmp_path / autofill.TARGET_CAPTURE_JSON_PATH)
    keys = {key.lower() for key in _iter_keys(capture)}
    allowed_safety_keys = {
        "no_probability_ev_edge_confidence_side_selection",
        "current_openrouter_review_status",
        "openrouter_calls_performed",
        "suitable_for_future_openrouter_batch",
    }
    forbidden = {
        "probability",
        "ev",
        "edge",
        "confidence",
        "confidence_score",
        "side_selection",
        "side-selection",
        "recommended_side",
        "buy_score",
        "sell_score",
    }

    assert forbidden.isdisjoint(keys - allowed_safety_keys)
    assert capture["auto_promote_to_ready_for_local_review"] is False
    assert capture["ready_for_local_review"] is False
    assert capture["current_readiness_band"] == "draft_from_readonly_candidate"


def test_created_capture_does_not_claim_official_source_if_missing_in_metadata(tmp_path):
    _prepare_root(tmp_path)
    normalized_path = tmp_path / autofill.NORMALIZED_CANDIDATE_PATH
    source_candidate_path = tmp_path / autofill.SOURCE_CANDIDATE_PATH
    normalized = _load_json(normalized_path)
    source_candidate = _load_json(source_candidate_path)
    normalized["official_weather_source_candidate"] = ""
    normalized["source_urls_or_references"] = []
    source_candidate["official_weather_source_identified"] = False
    source_candidate["official_source_references"] = []
    source_candidate["official_source_urls_or_rule_references"] = []
    _write_json(normalized_path, normalized)
    _write_json(source_candidate_path, source_candidate)

    packet = autofill.build_manual_capture_packet(tmp_path)

    assert packet["official_weather_source_identified"] is False
    assert any(
        "Official weather source was not identified" in item
        for item in packet["unresolved_source_questions"]
    )


def test_created_capture_has_weather_specific_fields_and_unresolved_questions(tmp_path):
    _prepare_root(tmp_path)
    autofill.write_autofill_artifacts(tmp_path)

    capture = _load_json(tmp_path / autofill.TARGET_CAPTURE_JSON_PATH)

    assert capture["location"] == "Arctic"
    assert capture["weather_metric"] == "minimum Arctic sea ice extent"
    assert capture["unit"] == "million_square_kilometers"
    assert capture["threshold_or_condition"] == "less than 4 million square kilometers"
    assert "August 1, 2026" in capture["date_or_time_window"]
    assert "October 1, 2026" in capture["date_or_time_window"]
    assert capture["official_weather_source_identified"] is True
    assert capture["station_or_source_hierarchy_identified"] is True
    assert any("timezone" in item.lower() for item in capture["unresolved_source_questions"])


def test_existing_validator_accepts_the_new_capture(tmp_path):
    _prepare_root(tmp_path)
    autofill.write_autofill_artifacts(tmp_path)

    report = validator.build_validation_report(tmp_path, market_id="693869")

    assert report["status"] == "manual_resolution_source_capture_validation_passed"
    assert report["total_packets_validated"] == 1
    assert report["invalid_count"] == 0
    assert report["packet_results"][0]["capture_status"] == "draft"


def test_source005_ingest_with_include_drafts_counts_693869(tmp_path):
    _prepare_root(tmp_path)
    autofill.write_autofill_artifacts(tmp_path)

    report = ingest.build_ingest_report(tmp_path, include_drafts=True)

    assert report["real_ingested_template_count"] == 1
    assert report["overlay"]["markets"][0]["market_id"] == "693869"
    assert report["overlay"]["canonical_packets_mutated"] is False


def test_source006_readiness_sees_three_real_ingested_drafts_and_keeps_gate_closed(tmp_path):
    _prepare_root(tmp_path)
    _copy_existing_capture(tmp_path, "597964")
    _copy_existing_capture(tmp_path, "1987056")
    _write_readiness_before(tmp_path)
    autofill.write_autofill_artifacts(tmp_path)
    ingest.write_ingest_artifacts(tmp_path, include_drafts=True)

    report = post_capture.write_post_capture_readiness_artifacts(tmp_path)

    assert report["real_ingested_template_count"] >= 3
    assert report["draft_ingested_template_count"] >= 3
    assert report["ready_ingested_template_count"] == 0
    assert "693869" in report["source_overlay_market_ids"]
    assert report["gate"]["future_live_002_allowed"] is False
    assert report["canonical_packets_mutated"] is False


def test_autofill_module_has_no_network_imports_or_calls():
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
    }
    forbidden_call_names = {"urlopen", "request", "post", "put", "patch", "delete"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Attribute):
            assert node.attr.lower() not in forbidden_call_names

    lowered = source.lower()
    assert "os.environ" not in lowered
    assert "getenv" not in lowered


def test_autofill_module_has_no_openrouter_api_path():
    source = MODULE_PATH.read_text(encoding="utf-8").lower()

    assert ("openrouter" + "_api_key") not in source
    assert ("openrouter" + ".ai") not in source
    assert ("api." + "openrouter") not in source
    assert ("author" + "ization") not in source
    assert ("bear" + "er ") not in source


def test_autofill_module_has_no_execution_runtime_or_queue_code_paths():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "subprocess",
        "webbrowser",
        "selenium",
        "playwright",
        "queue",
    }
    forbidden_function_tokens = (
        "wallet",
        "trade",
        "order",
        "dispatcher",
        "runtime",
        "background",
        "browser",
        "queue",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.FunctionDef):
            lowered_name = node.name.lower()
            assert all(token not in lowered_name for token in forbidden_function_tokens)


def test_source_quality_observation_candidate_does_not_score_source_by_profit(tmp_path):
    _prepare_root(tmp_path)
    autofill.write_autofill_artifacts(tmp_path)

    observation = _load_json(tmp_path / autofill.SOURCE_QUALITY_OBSERVATION_JSON_PATH)
    keys = {key.lower() for key in _iter_keys(observation)}

    assert observation["source_quality_status"] == "pending_capture_operator_review_and_outcome"
    assert observation["outcome_known"] is False
    assert observation["source_scoring_performed"] is False
    assert observation["source_ranking_updated"] is False
    assert observation["trading_profit_used_for_scoring"] is False
    assert observation["profit_or_pnl_recorded"] is False
    assert "profit_score" not in keys
    assert "betting_confidence" not in keys
    assert "edge" not in keys
    assert "ev" not in keys
    assert "recommendation" not in keys
    assert "recommended_side" not in keys


def test_passive_workbench_surface_exists_without_queue_runtime_dispatcher_changes(tmp_path):
    _prepare_root(tmp_path)
    autofill.write_autofill_artifacts(tmp_path)

    surface = _load_json(tmp_path / autofill.WORKBENCH_SURFACE_JSON_PATH)

    assert surface["draft_capture_available"] is True
    assert surface["source_quality_observation_candidate_available"] is True
    assert surface["no_market_action_guidance"] is True
    assert surface["no_trading_authority"] is True
    assert surface["queue_mutated"] is False
    assert surface["runtime_wiring_changed"] is False
    assert surface["dispatcher_changed"] is False


def test_existing_esports_state_remains_preserved():
    ingest_result = _load_json(INGEST_RESULT)
    gate = _load_json(READINESS_GATE)
    paperlive006 = _load_json(PAPERLIVE_006_RESULT)

    assert paperlive006["ready_for_weather_pilot"] is True
    assert paperlive006["ready_for_autonomous_trading"] is False
    assert ingest_result["real_ingested_template_count"] >= 3
    assert gate["real_ingested_template_count"] >= 3
    assert gate["draft_ingested_template_count"] >= 3
    assert gate["ready_ingested_template_count"] == 0
    assert gate["future_live_002_allowed"] is False
