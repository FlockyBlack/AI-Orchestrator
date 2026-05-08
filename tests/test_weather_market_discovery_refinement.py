import ast
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.live_readonly import weather_market_discovery as discovery  # noqa: E402


MODULE_PATH = ROOT / "pm_bot" / "live_readonly" / "weather_market_discovery.py"
INGEST_RESULT = ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_ingest_result.v1.json"
READINESS_GATE = ROOT / "pm_bot" / "llm" / "post_capture_batch_readiness_gate.v1.json"
PAPERLIVE_006_RESULT = ROOT / "docs" / "PMBOT_PAPERLIVE_006_RESULT.json"
HANDOFF = ROOT / "pm_bot" / "paper_live" / "esports_to_weather_handoff_readiness.v1.json"


class MockFetcher:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.urls = []

    def fetch_json(self, url):
        self.urls.append(url)
        if not self.payloads:
            raise AssertionError(f"unexpected fetch: {url}")
        return self.payloads.pop(0)


def _sample_weather_market():
    return {
        "id": "700201",
        "question": "Will NYC high temperature reach 90 degrees on May 15?",
        "slug": "will-nyc-high-temperature-reach-90-degrees-on-may-15",
        "resolutionSource": "https://www.weather.gov/okx/",
        "description": (
            "This market will resolve to Yes if the high temperature in NYC reaches "
            "at least 90 degrees Fahrenheit on May 15, 2026 by 11:59 PM ET. "
            "The resolution source for this market will be official information "
            "from the National Weather Service weather.gov station hierarchy, "
            "with Central Park weather station used as the measurement source. "
            "If the primary station is unavailable, operator review must verify "
            "the fallback source from the exact Polymarket rules."
        ),
        "outcomes": '["Yes", "No"]',
        "active": True,
        "closed": False,
    }


def _sample_sea_ice_market():
    return {
        "id": "700202",
        "question": (
            "Will the minimum Arctic sea ice extent this summer be less than "
            "4m square kilometers?"
        ),
        "slug": "will-the-minimum-arctic-sea-ice-extent-this-summer-be-less-than-4m",
        "resolutionSource": "https://nsidc.org/sea-ice-today/sea-ice-tools",
        "description": (
            "This market will resolve according to the minimum Arctic sea ice extent "
            "for all days between August 1, 2026 and October 1, 2026, as "
            "published by the National Snow and Ice Data Center. It resolves "
            "Yes if the extent is less than 4m square kilometers. If this "
            "resolution source becomes unavailable, another resolution source "
            "will be chosen after operator review."
        ),
        "outcomes": '["Yes", "No"]',
        "active": True,
        "closed": False,
    }


def _non_weather_market():
    return {
        "id": "1",
        "question": "Will a generic event happen by June 30?",
        "slug": "generic-event-by-june-30",
        "description": "This market is not about a weather measurement.",
        "outcomes": '["Yes", "No"]',
        "active": True,
        "closed": False,
    }


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


def _artifact_path(tmp_path, filename):
    return tmp_path / "pm_bot" / "live_readonly" / "weather_market_discovery" / filename


def test_010a2_dry_run_performs_zero_network_calls():
    payload = discovery.build_dry_run_status(max_calls=15, refined_search=True)

    assert payload["task_id"] == discovery.REFINED_TASK_ID
    assert payload["status"] == "dry_run_no_network"
    assert payload["refinement_attempt"] is True
    assert payload["network_allowed_explicitly"] is False
    assert payload["network_calls_performed"] == 0
    assert payload["polymarket_api_calls_performed"] == 0
    assert payload["fetch_performed"] is False
    assert payload["max_calls_hard_cap"] == 15


def test_010a2_fetch_mode_enforces_api_call_cap():
    fetcher = MockFetcher([[_non_weather_market()], [_sample_weather_market()]])

    payload = discovery.run_fetch_one(
        fetcher=fetcher,
        max_calls=1,
        page_limit=1,
        refined_search=True,
    )

    assert payload["fetch_status"] == "no_suitable_weather_market_found_after_refinement"
    assert payload["selected_market_id"] is None
    assert payload["network_call_count"] == 1
    assert len(fetcher.urls) == 1

    with pytest.raises(ValueError):
        discovery.run_fetch_one(fetcher=fetcher, max_calls=16, refined_search=True)


def test_010a2_fetch_mode_does_not_use_auth_headers_or_read_env_secrets():
    auth_header_name = "Author" + "ization"
    bearer_prefix = "Bear" + "er"
    assert auth_header_name not in discovery.PUBLIC_HEADERS
    assert bearer_prefix not in json.dumps(discovery.PUBLIC_HEADERS)

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_tokens = [
        "os.environ",
        "getenv",
        "openrouter" + "_api_key",
        "private" + "_key =",
        "private" + "_key=",
        "secret_key",
        "bearer" + " ",
        "author" + "ization",
    ]
    for token in forbidden_tokens:
        assert token not in lowered


def test_010a2_writes_refinement_diagnostics_and_preserves_010a_artifacts(tmp_path):
    previous_raw = _artifact_path(tmp_path, discovery.RAW_FETCH_JSON)
    previous_raw.parent.mkdir(parents=True, exist_ok=True)
    previous_raw.write_text('{"sentinel":"010a"}\n', encoding="utf-8")

    payload = discovery.run_fetch_one(
        write=True,
        fetcher=MockFetcher([[_sample_weather_market()]]),
        max_calls=1,
        root=tmp_path,
        refined_search=True,
    )

    assert payload["fetch_status"] == "selected"
    assert previous_raw.read_text(encoding="utf-8") == '{"sentinel":"010a"}\n'
    assert _artifact_path(tmp_path, discovery.REFINED_DIAGNOSTICS_JSON).exists()
    diagnostics = _load_json(_artifact_path(tmp_path, discovery.REFINED_DIAGNOSTICS_JSON))
    assert diagnostics["previous_attempt_result_path"] == discovery.PREVIOUS_ATTEMPT_RESULT_PATH
    assert diagnostics["diagnostics_available" if False else "no_market_action_guidance"] is True


def test_010a2_candidate_found_has_weather_class_and_no_trading_fields(tmp_path):
    discovery.run_fetch_one(
        write=True,
        fetcher=MockFetcher([[_sample_weather_market()]]),
        max_calls=1,
        root=tmp_path,
        refined_search=True,
    )
    normalized = _load_json(_artifact_path(tmp_path, discovery.REFINED_NORMALIZED_JSON))
    result = _load_json(tmp_path / discovery.REFINED_RESULT_JSON)

    assert normalized["market_class"] == "weather"
    assert normalized["market_id"] == "700201"
    assert result["selected_market_id"] == "700201"
    assert result["orders_created"] is False
    assert result["simulated_trade_created"] is False
    assert result["selected_side"] is None
    assert result["stake_amount"] is None
    assert result["wallet_or_private_key_accessed"] is False
    assert result["market_action_guidance_generated"] is False


def test_010a2_no_candidate_found_does_not_force_selection(tmp_path):
    payload = discovery.run_fetch_one(
        write=True,
        fetcher=MockFetcher([[_non_weather_market()]]),
        max_calls=1,
        page_limit=1,
        root=tmp_path,
        refined_search=True,
    )
    raw = _load_json(_artifact_path(tmp_path, discovery.REFINED_RAW_FETCH_JSON))
    normalized = _load_json(_artifact_path(tmp_path, discovery.REFINED_NORMALIZED_JSON))
    source_capture = _load_json(_artifact_path(tmp_path, discovery.REFINED_SOURCE_CAPTURE_JSON))

    assert payload["status"] == "no_suitable_weather_market_found_after_refinement"
    assert payload["fetch_status"] == "no_suitable_weather_market_found_after_refinement"
    assert payload["selected_market_id"] is None
    assert raw["fetch_status"] == "no_suitable_weather_market_found_after_refinement"
    assert raw["selected_market_id"] is None
    assert normalized["market_id"] is None
    assert normalized["status"] == "no_suitable_weather_market_found_after_refinement"
    assert source_capture["status"] == "no_candidate"


def test_refined_normalized_candidate_has_weather_specific_fields(tmp_path):
    discovery.run_fetch_one(
        write=True,
        fetcher=MockFetcher([[_sample_sea_ice_market()]]),
        max_calls=1,
        root=tmp_path,
        refined_search=True,
    )
    normalized = _load_json(_artifact_path(tmp_path, discovery.REFINED_NORMALIZED_JSON))

    assert normalized["market_class"] == "weather"
    assert normalized["location"] == "Arctic"
    assert normalized["weather_metric"] == "sea_ice_extent"
    assert normalized["unit"] == "million_square_kilometers"
    assert normalized["threshold_or_condition"]
    assert normalized["date_or_time_window"]
    assert normalized["official_weather_source_candidate"]
    assert normalized["operator_review_required"] is True
    assert normalized["planned_capture_status"] == "draft"
    assert normalized["auto_promote_to_ready_for_local_review"] is False


def test_refined_source_capture_candidate_is_draft_only_and_cannot_auto_promote(tmp_path):
    discovery.run_fetch_one(
        write=True,
        fetcher=MockFetcher([[_sample_weather_market()]]),
        max_calls=1,
        root=tmp_path,
        refined_search=True,
    )
    source_capture = _load_json(_artifact_path(tmp_path, discovery.REFINED_SOURCE_CAPTURE_JSON))

    assert source_capture["planned_source_capture_status"] == "draft"
    assert source_capture["planned_capture_status"] == "draft"
    assert source_capture["auto_fill_allowed_only_as_draft"] is True
    assert source_capture["auto_promote_to_ready_for_local_review"] is False
    assert source_capture["operator_review_required"] is True


def test_refined_checklist_has_weather_specific_review_items(tmp_path):
    discovery.run_fetch_one(
        write=True,
        fetcher=MockFetcher([[_sample_weather_market()]]),
        max_calls=1,
        root=tmp_path,
        refined_search=True,
    )
    checklist = _load_json(_artifact_path(tmp_path, discovery.REFINED_CHECKLIST_JSON))
    check_ids = {item["check_id"] for item in checklist["checklist"]}

    assert {
        "verify_exact_polymarket_rules_text",
        "verify_location",
        "verify_weather_metric",
        "verify_unit",
        "verify_threshold_or_condition",
        "verify_date_or_time_window",
        "verify_timezone",
        "verify_official_weather_source",
        "verify_station_or_source_hierarchy",
        "verify_fallback_source",
        "verify_source_capture_promotion_readiness",
        "no_trading_decision",
    }.issubset(check_ids)


def test_source_quality_observation_candidate_does_not_score_source_by_profit(tmp_path):
    discovery.run_fetch_one(
        write=True,
        fetcher=MockFetcher([[_sample_weather_market()]]),
        max_calls=1,
        root=tmp_path,
        refined_search=True,
    )
    candidate = _load_json(tmp_path / discovery.REFINED_SOURCE_QUALITY_JSON)
    keys = {key.lower() for key in _iter_keys(candidate)}

    assert candidate["status"] == "pending_future_capture_and_outcome_review"
    assert candidate["outcome_known"] is False
    assert candidate["source_scoring_performed"] is False
    assert candidate["source_ranking_updated"] is False
    assert candidate["trading_profit_used_for_scoring"] is False
    assert "profit_score" not in keys
    assert "profitable_trade_count" not in keys
    assert "roi" not in keys
    assert "pnl" not in keys


def test_result_artifacts_have_no_prediction_or_side_selection_guidance(tmp_path):
    discovery.run_fetch_one(
        write=True,
        fetcher=MockFetcher([[_sample_weather_market()]]),
        max_calls=1,
        root=tmp_path,
        refined_search=True,
    )
    result = _load_json(tmp_path / discovery.REFINED_RESULT_JSON)

    assert result["probability_ev_edge_confidence_generated"] is False
    assert result["side_selection_generated"] is False
    assert result["market_action_guidance_generated"] is False
    assert result["selected_side"] is None
    assert result["stake_amount"] is None
    assert result["simulated_trade_created"] is False


def test_no_openrouter_wallet_order_runtime_dispatcher_queue_or_browser_path():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "webbrowser",
        "selenium",
        "playwright",
        "queue",
    }
    forbidden_call_names = {"post", "put", "patch", "delete"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Attribute):
            assert node.attr.lower() not in forbidden_call_names

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    assert ("openrouter" + "_api_key") not in source
    assert ("api." + "openrouter") not in source
    assert ("openrouter" + ".ai") not in source
    assert 'method="get"' in source
    for token in (
        'method="' + "post" + '"',
        'method="' + "patch" + '"',
        "clob" + ".polymarket",
    ):
        assert token not in source


def test_existing_esports_and_source_state_remains_preserved():
    ingest = _load_json(INGEST_RESULT)
    gate = _load_json(READINESS_GATE)
    paperlive006 = _load_json(PAPERLIVE_006_RESULT)
    handoff = _load_json(HANDOFF)

    assert handoff["weather_pilot_allowed"] is True
    assert paperlive006["ready_for_weather_pilot"] is True
    assert paperlive006["ready_for_autonomous_trading"] is False
    assert ingest["real_ingested_template_count"] >= 2
    assert gate["real_ingested_template_count"] >= 2
    assert gate["draft_ingested_template_count"] >= 2
    assert gate["ready_ingested_template_count"] == 0
    assert gate["future_live_002_allowed"] is False
