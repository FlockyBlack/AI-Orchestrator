import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

OPERATOR_SURFACE_JSON = (
    ROOT / "pm_bot" / "llm" / "esports_operator_review_surface_1987056_009c.v1.json"
)
OPERATOR_SURFACE_MD = (
    ROOT / "pm_bot" / "llm" / "esports_operator_review_surface_1987056_009c.v1.md"
)
LEDGER_CONTRACT_JSON = (
    ROOT / "pm_bot" / "paper_live" / "paper_live_observation_ledger_contract.v1.json"
)
LEDGER_CONTRACT_MD = (
    ROOT / "pm_bot" / "paper_live" / "paper_live_observation_ledger_contract.v1.md"
)
OBSERVATION_PLAN_JSON = (
    ROOT / "pm_bot" / "paper_live" / "esports_observation_plan_1987056_009c.v1.json"
)
OBSERVATION_PLAN_MD = (
    ROOT / "pm_bot" / "paper_live" / "esports_observation_plan_1987056_009c.v1.md"
)
OUTCOME_CONTRACT_JSON = ROOT / "pm_bot" / "paper_live" / "outcome_tracking_contract.v1.json"
OUTCOME_CONTRACT_MD = ROOT / "pm_bot" / "paper_live" / "outcome_tracking_contract.v1.md"
SOURCE_FLOW_JSON = ROOT / "pm_bot" / "llm" / "source_quality_observation_flow_009c.v1.json"
SOURCE_FLOW_MD = ROOT / "pm_bot" / "llm" / "source_quality_observation_flow_009c.v1.md"
WORKBENCH_JSON = (
    ROOT / "pm_bot" / "workbench" / "esports_paper_live_preparation_surface_1987056_009c.v1.json"
)
WORKBENCH_MD = (
    ROOT / "pm_bot" / "workbench" / "esports_paper_live_preparation_surface_1987056_009c.v1.md"
)
RESULT_JSON = ROOT / "docs" / "PMBOT_SOURCE_009C_RESULT.json"
RESULT_MD = (
    ROOT
    / "docs"
    / "PMBOT_SOURCE_009C_ESPORTS_OPERATOR_REVIEW_SURFACE_AND_PAPERLIVE_PREPARATION.md"
)
READINESS_REPORT = ROOT / "pm_bot" / "llm" / "post_capture_readiness_report.v1.json"
READINESS_GATE = ROOT / "pm_bot" / "llm" / "post_capture_batch_readiness_gate.v1.json"

NEW_JSON_ARTIFACTS = [
    OPERATOR_SURFACE_JSON,
    LEDGER_CONTRACT_JSON,
    OBSERVATION_PLAN_JSON,
    OUTCOME_CONTRACT_JSON,
    SOURCE_FLOW_JSON,
    WORKBENCH_JSON,
    RESULT_JSON,
]

NEW_TEXT_ARTIFACTS = [
    OPERATOR_SURFACE_MD,
    LEDGER_CONTRACT_MD,
    OBSERVATION_PLAN_MD,
    OUTCOME_CONTRACT_MD,
    SOURCE_FLOW_MD,
    WORKBENCH_MD,
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


def test_operator_review_surface_exists_and_references_market_1987056():
    payload = _load_json(OPERATOR_SURFACE_JSON)
    markdown = OPERATOR_SURFACE_MD.read_text(encoding="utf-8")

    assert payload["market_id"] == "1987056"
    assert payload["market_class"] == "esports"
    assert "JD Gaming vs Anyone's Legend" in payload["title_or_question"]
    assert "1987056" in markdown


def test_operator_review_surface_is_draft_and_not_ready_for_local_review():
    payload = _load_json(OPERATOR_SURFACE_JSON)

    assert payload["capture_status"] == "draft"
    assert payload["source_capture_status"] == "draft"
    assert payload["operator_review_required"] is True
    assert payload["ready_for_local_review"] is False
    assert payload["paper_live_preparation_status"]["simulated_decision_ready"] is False


def test_paper_live_ledger_contract_exists():
    payload = _load_json(LEDGER_CONTRACT_JSON)

    assert payload["contract_version"] == "paper_live_observation_ledger_contract.v1"
    assert payload["market_id"] == "1987056"
    assert payload["paper_live_mode"] == "observation_only"
    assert LEDGER_CONTRACT_MD.read_text(encoding="utf-8")


def test_paper_live_contract_has_no_simulated_trade():
    payload = _load_json(LEDGER_CONTRACT_JSON)

    assert payload["simulated_trade_created"] is False
    assert payload["order_created"] is False
    assert payload["wallet_used"] is False


def test_paper_live_contract_has_null_selected_side_and_stake_amount():
    payload = _load_json(LEDGER_CONTRACT_JSON)

    assert payload["selected_side"] is None
    assert payload["stake_amount"] is None
    assert payload["safety_summary"]["selected_side_is_null_by_contract"] is True
    assert payload["safety_summary"]["stake_amount_is_null_by_contract"] is True


def test_paper_live_observation_plan_exists_for_1987056():
    payload = _load_json(OBSERVATION_PLAN_JSON)

    assert payload["schema_version"] == "esports_observation_plan_1987056_009c.v1"
    assert payload["market_id"] == "1987056"
    assert payload["market_class"] == "esports"
    assert payload["observation_mode"] == "source_and_outcome_tracking_only"


def test_observation_plan_does_not_select_side_or_recommend_action():
    payload = _load_json(OBSERVATION_PLAN_JSON)
    keys = {key.lower() for key in _iter_keys(payload)}

    assert payload["ready_for_simulated_decision"] is False
    assert payload["simulated_decision_created"] is False
    assert payload["selected_side"] is None
    assert payload["stake_amount"] is None
    assert payload["no_market_action_guidance"] is True
    assert "recommended_side" not in keys
    assert "side_selection" not in keys


def test_outcome_tracking_contract_exists_and_forbids_profit_based_source_learning():
    payload = _load_json(OUTCOME_CONTRACT_JSON)
    forbidden_learning_inputs = " ".join(payload["forbidden_learning_inputs"]).lower()

    assert payload["contract_version"] == "outcome_tracking_contract.v1"
    assert payload["tracking_scope"] == "outcome_and_source_alignment_only"
    assert payload["trading_profit_used_for_source_scoring"] is False
    assert payload["safety_summary"]["not_profit_loss_tracking"] is True
    assert "trading profit" in forbidden_learning_inputs
    assert "financial return" in forbidden_learning_inputs


def test_source_quality_observation_flow_exists_and_forbids_profit_only_source_scoring():
    payload = _load_json(SOURCE_FLOW_JSON)
    allowed_fields = set(payload["allowed_future_source_quality_fields"])

    assert payload["schema_version"] == "source_quality_observation_flow_009c.v1"
    assert payload["market_id"] == "1987056"
    assert payload["future_use_boundary"]["profit_only_source_scoring_allowed"] is False
    assert payload["future_use_boundary"]["source_ranking_for_trading_decisions_created"] is False
    assert allowed_fields == {
        "resolution_alignment_count",
        "contradiction_count",
        "timeliness_notes",
        "official_source_status",
        "operator_usefulness_notes",
    }


def test_no_forbidden_fields_exist_in_new_json_artifacts():
    forbidden_exact_keys = {
        "probability",
        "ev",
        "edge",
        "confidence",
        "side_selection",
        "buy",
        "sell",
        "hold",
        "enter",
        "exit",
        "recommendation",
    }

    for path in NEW_JSON_ARTIFACTS:
        keys = {key.lower() for key in _iter_keys(_load_json(path))}
        assert forbidden_exact_keys.isdisjoint(keys), path


def test_forbidden_terms_only_appear_in_explicit_safety_context():
    forbidden_terms = [
        "probability",
        "ev",
        "edge",
        "confidence",
        "side_selection",
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
        "forbidden",
        "must not",
        "does not",
        "do not",
        "without",
        "_allowed",
        "_generated",
        "is_null",
    )

    for path, text in _all_new_artifact_lines():
        for line in text.splitlines():
            lowered = line.lower()
            for term in forbidden_terms:
                if re.search(rf"\b{re.escape(term.lower())}\b", lowered):
                    assert any(marker in lowered for marker in safety_markers), (path, line)


def test_no_openrouter_api_network_wallet_order_runtime_dispatcher_queue_or_browser_behavior_added():
    sensitive_patterns = [
        "openrouter_api_key",
        "sk-",
        "begin private key",
        "authorization",
        "bearer ",
        "requests.",
        "httpx.",
        "aiohttp",
        "urlopen",
        "socket.",
        "subprocess.",
        "selenium",
        "playwright",
        "webbrowser",
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
        _load_json(LEDGER_CONTRACT_JSON)["safety_summary"],
        _load_json(OBSERVATION_PLAN_JSON)["safety_summary"],
        _load_json(OUTCOME_CONTRACT_JSON)["safety_summary"],
        _load_json(SOURCE_FLOW_JSON)["safety_summary"],
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


def test_workbench_surface_is_standalone_passive_artifact():
    payload = _load_json(WORKBENCH_JSON)

    assert payload["market_id"] == "1987056"
    assert payload["source_capture_status"] == "draft"
    assert payload["operator_review_required"] is True
    assert payload["paper_live_contract_available"] is True
    assert payload["observation_plan_available"] is True
    assert payload["outcome_tracking_contract_available"] is True
    assert payload["source_quality_flow_available"] is True
    assert payload["no_trading_authority"] is True
    assert payload["queue_mutated"] is False
    assert payload["runtime_wiring_changed"] is False
    assert payload["dispatcher_changed"] is False


def test_source_009b_counts_are_preserved():
    report = _load_json(READINESS_REPORT)
    gate = _load_json(READINESS_GATE)

    assert report["real_ingested_template_count"] >= 2
    assert report["draft_ingested_template_count"] >= 2
    assert report["ready_ingested_template_count"] == 0
    assert gate["future_live_002_allowed"] is False
    assert gate["real_ingested_template_count"] >= 2
    assert gate["draft_ingested_template_count"] >= 2
    assert gate["ready_ingested_template_count"] == 0
