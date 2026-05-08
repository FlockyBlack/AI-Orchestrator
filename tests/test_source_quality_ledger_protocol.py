import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_JSON = ROOT / "pm_bot" / "llm" / "source_quality_ledger_protocol.v1.json"
PROTOCOL_MD = ROOT / "pm_bot" / "llm" / "source_quality_ledger_protocol.v1.md"


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


def test_source_quality_ledger_protocol_exists_and_is_valid_json():
    payload = _load_json(PROTOCOL_JSON)

    assert payload["schema_version"] == "source_quality_ledger_protocol.v1"
    assert payload["status"] == "protocol_only_no_trading_performance_learning"
    assert PROTOCOL_MD.read_text(encoding="utf-8")


def test_source_quality_ledger_tracks_resolution_capture_quality_not_profit_only():
    payload = _load_json(PROTOCOL_JSON)
    text = json.dumps(payload, sort_keys=True).lower()
    md_text = PROTOCOL_MD.read_text(encoding="utf-8").lower()

    assert "trade profit as sole source quality score" in text
    assert "should not be rewarded merely because a trade was profitable" in text
    assert "should not rank a source just because a trade later made money" in md_text
    assert "resolution alignment" in payload["future_scoring_inputs_allowed"]
    assert "timeliness" in payload["future_scoring_inputs_allowed"]
    assert "official/source hierarchy" in payload["future_scoring_inputs_allowed"]
    assert "contradiction rate" in payload["future_scoring_inputs_allowed"]
    assert "usefulness for rules/source capture" in payload["future_scoring_inputs_allowed"]
    assert "operator review usefulness" in payload["future_scoring_inputs_allowed"]


def test_source_quality_ledger_has_allowed_future_fields_only_for_protocol_shape():
    payload = _load_json(PROTOCOL_JSON)
    allowed = set(payload["allowed_future_fields"])
    expected = {
        "source_id",
        "source_type",
        "market_class",
        "markets_used_count",
        "resolved_markets_count",
        "resolution_alignment_count",
        "misleading_count",
        "timeliness_notes",
        "source_reliability_notes",
        "operator_review_notes",
    }

    assert expected == allowed


def test_source_quality_ledger_forbids_market_action_and_execution_authority():
    payload = _load_json(PROTOCOL_JSON)
    forbidden = " ".join(payload["forbidden_future_uses"]).lower()
    safety = payload["safety_summary"]

    assert "buy or sell recommendation" in forbidden
    assert "edge, ev, probability, or confidence scoring" in forbidden
    assert "side selection" in forbidden
    assert "autonomous execution authority" in forbidden
    assert "wallet or order authority" in forbidden
    assert safety["openrouter_calls_performed"] == 0
    assert safety["authenticated_endpoints_used"] is False
    assert safety["wallet_or_private_key_accessed"] is False
    assert safety["orders_created"] is False
    assert safety["market_action_guidance_generated"] is False
    assert safety["probability_ev_edge_confidence_generated"] is False
    assert safety["side_selection_generated"] is False
    assert safety["autonomous_execution_authority"] is False


def test_source_quality_ledger_does_not_define_profit_or_market_decision_score_fields():
    payload = _load_json(PROTOCOL_JSON)
    keys = {key.lower() for key in _iter_keys(payload)}
    forbidden_keys = {
        "profit_score",
        "profitable_trade_score",
        "buy_score",
        "sell_score",
        "edge_score",
        "ev_score",
        "probability_score",
        "confidence_score",
        "recommended_side",
        "execution_authority",
    }

    assert forbidden_keys.isdisjoint(keys)
