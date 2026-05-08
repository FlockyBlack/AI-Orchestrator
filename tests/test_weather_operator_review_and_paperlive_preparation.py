import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

OPERATOR_SURFACE_JSON = (
    ROOT / "pm_bot" / "llm" / "weather_operator_review_surface_693869_010c.v1.json"
)
OPERATOR_SURFACE_MD = (
    ROOT / "pm_bot" / "llm" / "weather_operator_review_surface_693869_010c.v1.md"
)
OBSERVATION_PLAN_JSON = (
    ROOT / "pm_bot" / "paper_live" / "weather_observation_plan_693869_010c.v1.json"
)
OBSERVATION_PLAN_MD = (
    ROOT / "pm_bot" / "paper_live" / "weather_observation_plan_693869_010c.v1.md"
)
OUTCOME_CONTRACT_JSON = (
    ROOT / "pm_bot" / "paper_live" / "weather_outcome_tracking_contract_693869_010c.v1.json"
)
OUTCOME_CONTRACT_MD = (
    ROOT / "pm_bot" / "paper_live" / "weather_outcome_tracking_contract_693869_010c.v1.md"
)
SOURCE_FLOW_JSON = (
    ROOT / "pm_bot" / "llm" / "weather_source_quality_observation_flow_010c.v1.json"
)
SOURCE_FLOW_MD = (
    ROOT / "pm_bot" / "llm" / "weather_source_quality_observation_flow_010c.v1.md"
)
WORKBENCH_JSON = (
    ROOT / "pm_bot" / "workbench" / "weather_paper_live_preparation_surface_693869_010c.v1.json"
)
WORKBENCH_MD = (
    ROOT / "pm_bot" / "workbench" / "weather_paper_live_preparation_surface_693869_010c.v1.md"
)
SUMMARY_JSON = (
    ROOT / "pm_bot" / "paper_live" / "weather_paperlive_preparation_summary_693869_010c.v1.json"
)
SUMMARY_MD = (
    ROOT / "pm_bot" / "paper_live" / "weather_paperlive_preparation_summary_693869_010c.v1.md"
)
RESULT_JSON = ROOT / "docs" / "PMBOT_SOURCE_010C_RESULT.json"
RESULT_MD = (
    ROOT
    / "docs"
    / "PMBOT_SOURCE_010C_WEATHER_OPERATOR_REVIEW_SURFACE_AND_PAPERLIVE_PREPARATION.md"
)
READINESS_REPORT = ROOT / "pm_bot" / "llm" / "post_capture_readiness_report.v1.json"
READINESS_GATE = ROOT / "pm_bot" / "llm" / "post_capture_batch_readiness_gate.v1.json"
PAPERLIVE_006_RESULT = ROOT / "docs" / "PMBOT_PAPERLIVE_006_RESULT.json"

NEW_JSON_ARTIFACTS = [
    OPERATOR_SURFACE_JSON,
    OBSERVATION_PLAN_JSON,
    OUTCOME_CONTRACT_JSON,
    SOURCE_FLOW_JSON,
    WORKBENCH_JSON,
    SUMMARY_JSON,
    RESULT_JSON,
]

NEW_TEXT_ARTIFACTS = [
    OPERATOR_SURFACE_MD,
    OBSERVATION_PLAN_MD,
    OUTCOME_CONTRACT_MD,
    SOURCE_FLOW_MD,
    WORKBENCH_MD,
    SUMMARY_MD,
    RESULT_MD,
]


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield key
            yield from _iter_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_keys(item)


def _iter_string_values(payload):
    if isinstance(payload, dict):
        for value in payload.values():
            yield from _iter_string_values(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_string_values(item)
    elif isinstance(payload, str):
        yield payload


def _all_new_artifact_lines():
    for path in NEW_JSON_ARTIFACTS:
        yield path, json.dumps(_load_json(path), indent=2, sort_keys=True)
    for path in NEW_TEXT_ARTIFACTS:
        yield path, path.read_text(encoding="utf-8")


def test_weather_operator_review_surface_exists_and_references_market_693869():
    payload = _load_json(OPERATOR_SURFACE_JSON)
    markdown = OPERATOR_SURFACE_MD.read_text(encoding="utf-8")

    assert payload["market_id"] == "693869"
    assert payload["market_class"] == "weather"
    assert "Arctic sea ice extent" in payload["title_or_question"]
    assert "693869" in markdown


def test_weather_operator_review_surface_is_draft_and_not_ready_for_local_review():
    payload = _load_json(OPERATOR_SURFACE_JSON)

    assert payload["capture_status"] == "draft"
    assert payload["source_capture_status"] == "draft"
    assert payload["operator_review_required"] is True
    assert payload["ready_for_local_review"] is False
    assert payload["paper_live_preparation_status"]["ready_for_simulated_decision"] is False


def test_weather_operator_review_surface_includes_weather_specific_fields():
    payload = _load_json(OPERATOR_SURFACE_JSON)
    known = payload["known_fields"]

    expected_fields = {
        "location",
        "weather_metric",
        "unit",
        "threshold_or_condition",
        "date_or_time_window",
        "timezone",
        "official_weather_source",
        "station_or_source_hierarchy",
        "fallback_source",
        "source_timestamp",
    }
    assert expected_fields.issubset(known)
    assert known["location"] == "Arctic"
    assert "sea ice extent" in known["weather_metric"]
    assert "timezone" in payload["missing_fields"]


def test_weather_observation_plan_exists_for_693869():
    payload = _load_json(OBSERVATION_PLAN_JSON)

    assert payload["schema_version"] == "weather_observation_plan_693869_010c.v1"
    assert payload["market_id"] == "693869"
    assert payload["market_class"] == "weather"
    assert payload["observation_mode"] == "source_and_outcome_tracking_only"


def test_observation_plan_has_no_simulated_decision_side_or_stake():
    payload = _load_json(OBSERVATION_PLAN_JSON)

    assert payload["ready_for_simulated_decision"] is False
    assert payload["simulated_decision_created"] is False
    assert payload["selected_side"] is None
    assert payload["stake_amount"] is None


def test_observation_plan_does_not_recommend_market_action():
    payload = _load_json(OBSERVATION_PLAN_JSON)
    keys = {key.lower() for key in _iter_keys(payload)}
    text = OBSERVATION_PLAN_MD.read_text(encoding="utf-8").lower()

    assert payload["no_market_action_guidance"] is True
    assert payload["no_trading_authority"] is True
    assert "recommended_side" not in keys
    assert "side_selection" not in keys
    assert "does not provide betting action" in text


def test_weather_outcome_tracking_contract_exists_and_forbids_profit_based_source_learning():
    payload = _load_json(OUTCOME_CONTRACT_JSON)
    forbidden_inputs = " ".join(payload["forbidden_learning_inputs"]).lower()

    assert payload["contract_version"] == "weather_outcome_tracking_contract_693869_010c.v1"
    assert payload["tracking_scope"] == "weather_outcome_and_source_alignment_only"
    assert payload["outcome_known"] is False
    assert payload["trading_profit_used_for_source_scoring"] is False
    assert payload["safety_summary"]["not_profit_loss_tracking"] is True
    assert "no profit" in forbidden_inputs
    assert "no pnl" in forbidden_inputs
    assert "no roi" in forbidden_inputs


def test_weather_source_quality_observation_flow_exists_and_forbids_profit_only_source_scoring():
    payload = _load_json(SOURCE_FLOW_JSON)
    roles = set(payload["weather_source_roles"])
    allowed = set(payload["allowed_future_scoring"])

    assert payload["schema_version"] == "weather_source_quality_observation_flow_010c.v1"
    assert payload["market_id"] == "693869"
    assert payload["future_use_boundary"]["profit_only_source_scoring_allowed"] is False
    assert payload["future_use_boundary"]["source_ranking_for_trading_decisions_created"] is False
    assert {
        "market_metadata_source",
        "market_rules_source",
        "official_weather_source_candidate",
        "station_or_dataset_source_candidate",
        "fallback_weather_source_candidate",
        "unresolved_source",
        "local_capture_source",
        "operator_review_surface",
    }.issubset(roles)
    assert allowed == {
        "resolution_alignment",
        "measurement_alignment",
        "timeliness",
        "official_source_status",
        "contradiction_count",
        "operator_usefulness_notes",
    }


def test_passive_workbench_weather_preparation_surface_does_not_create_queue_runtime_or_dispatcher_changes():
    payload = _load_json(WORKBENCH_JSON)

    assert payload["market_id"] == "693869"
    assert payload["source_capture_status"] == "draft"
    assert payload["operator_review_required"] is True
    assert payload["paper_live_observation_plan_available"] is True
    assert payload["weather_outcome_tracking_contract_available"] is True
    assert payload["source_quality_flow_available"] is True
    assert payload["no_trading_authority"] is True
    assert payload["no_market_action_guidance"] is True
    assert payload["queue_created"] is False
    assert payload["queue_mutated"] is False
    assert payload["runtime_wiring_changed"] is False
    assert payload["dispatcher_changed"] is False


def test_weather_preparation_summary_exists():
    payload = _load_json(SUMMARY_JSON)

    assert payload["market_id"] == "693869"
    assert payload["operator_review_surface_created"] is True
    assert payload["observation_plan_created"] is True
    assert payload["outcome_tracking_contract_created"] is True
    assert payload["source_quality_flow_created"] is True
    assert payload["passive_workbench_surface_created"] is True
    assert payload["ready_for_simulated_decision"] is False
    assert payload["simulated_trade_created"] is False
    assert payload["selected_side"] is None
    assert payload["stake_amount"] is None


def test_no_forbidden_exact_fields_exist_in_new_artifacts():
    forbidden_exact_keys = {
        "proba" + "bility",
        "e" + "v",
        "ed" + "ge",
        "confi" + "dence",
        "b" + "uy",
        "se" + "ll",
        "ho" + "ld",
        "en" + "ter",
        "ex" + "it",
        "recomm" + "endation",
    }
    allowed_keys = {
        "selected_side",
        "side_selection_generated",
        "probability_ev_edge_confidence_generated",
        "next_recommended_action",
    }

    for path in NEW_JSON_ARTIFACTS:
        keys = {key.lower() for key in _iter_keys(_load_json(path))}
        assert forbidden_exact_keys.isdisjoint(keys - allowed_keys), path


def test_forbidden_terms_only_appear_in_explicit_safety_context():
    forbidden_terms = [
        "proba" + "bility",
        "E" + "V",
        "ed" + "ge",
        "confi" + "dence",
        "side " + "selection",
        "side-" + "selection",
        "b" + "uy",
        "se" + "ll",
        "ho" + "ld",
        "en" + "ter",
        "ex" + "it",
        "recomm" + "endation",
    ]
    safety_markers = (
        "no ",
        "not ",
        "null",
        "false",
        "forbidden",
        "must not",
        "does not",
        "do not",
        "without",
        "_generated",
        "_allowed",
        "_authority",
        "safety",
    )

    for path, text in _all_new_artifact_lines():
        for line in text.splitlines():
            lowered = line.lower()
            for term in forbidden_terms:
                if re.search(rf"\b{re.escape(term.lower())}\b", lowered):
                    assert any(marker in lowered for marker in safety_markers), (path, line)


def test_no_openrouter_api_network_wallet_order_runtime_dispatcher_queue_or_browser_behavior_introduced():
    sensitive_patterns = [
        "openrouter" + "_api_key",
        "s" + "k-",
        "begin " + "private key",
        "author" + "ization",
        "bear" + "er ",
        "requests" + ".",
        "httpx" + ".",
        "aio" + "http",
        "url" + "open",
        "socket" + ".",
        "subprocess" + ".",
        "sele" + "nium",
        "play" + "wright",
        "web" + "browser",
    ]

    for path, text in _all_new_artifact_lines():
        lowered = text.lower()
        for pattern in sensitive_patterns:
            assert pattern not in lowered, (path, pattern)

    for path in NEW_JSON_ARTIFACTS:
        payload = _load_json(path)
        values = {value.lower() for value in _iter_string_values(payload)}
        assert "authenticated endpoint" not in values

    safety_payloads = [
        _load_json(OPERATOR_SURFACE_JSON)["safety_summary"],
        _load_json(OBSERVATION_PLAN_JSON)["safety_summary"],
        _load_json(OUTCOME_CONTRACT_JSON)["safety_summary"],
        _load_json(SOURCE_FLOW_JSON)["safety_summary"],
        _load_json(SUMMARY_JSON)["safety_summary"],
    ]
    for safety in safety_payloads:
        assert safety["openrouter_calls_performed"] == 0
        assert safety["polymarket_api_calls_performed"] == 0
        assert safety["external_network_calls_performed"] == 0
        assert safety["authenticated_endpoints_used"] is False
        assert safety["wallet_or_private_key_accessed"] is False
        assert safety["orders_created"] is False
        assert safety["trading_runtime_changed"] is False
        assert safety["dispatcher_changed"] is False
        assert safety["background_worker_created"] is False
        assert safety["queue_mutated"] is False
        assert safety["browser_automation_used"] is False
        assert safety["canonical_packets_mutated"] is False


def test_existing_source_010b_counts_are_preserved():
    report = _load_json(READINESS_REPORT)
    gate = _load_json(READINESS_GATE)

    assert report["real_ingested_template_count"] >= 3
    assert report["draft_ingested_template_count"] >= 3
    assert report["ready_ingested_template_count"] == 0
    assert gate["real_ingested_template_count"] >= 3
    assert gate["draft_ingested_template_count"] >= 3
    assert gate["ready_ingested_template_count"] == 0
    assert gate["future_live_002_allowed"] is False


def test_ready_for_autonomous_trading_remains_false():
    paperlive006 = _load_json(PAPERLIVE_006_RESULT)
    summary = _load_json(SUMMARY_JSON)
    result = _load_json(RESULT_JSON)

    assert paperlive006["ready_for_autonomous_trading"] is False
    assert summary["safety_summary"]["ready_for_autonomous_trading"] is False
    assert result["ready_for_autonomous_trading"] is False
