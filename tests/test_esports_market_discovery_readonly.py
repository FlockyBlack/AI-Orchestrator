import ast
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pm_bot.live_readonly import esports_market_discovery as discovery

MODULE_PATH = ROOT / "pm_bot" / "live_readonly" / "esports_market_discovery.py"
SOURCE_007_INGEST = (
    ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_ingest_result.v1.json"
)
SOURCE_007_GATE = ROOT / "pm_bot" / "llm" / "post_capture_batch_readiness_gate.v1.json"


class MockFetcher:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.urls = []

    def fetch_json(self, url):
        self.urls.append(url)
        if not self.payloads:
            raise AssertionError(f"unexpected fetch: {url}")
        return self.payloads.pop(0)


def _sample_event():
    market = {
        "id": "2121194",
        "question": "LoL: G2 Esports vs Natus Vincere (BO3) - Esports World Cup EMEA Qualifier Playoffs",
        "slug": "lol-g2-navi-2026-05-14",
        "resolutionSource": "https://gol.gg/esports/home",
        "description": (
            "This market refers to the LoL Upper bracket semifinal 1 match between "
            "G2 Esports and Natus Vincere in the Esports World Cup EMEA Qualifier "
            "Playoffs, initially scheduled for May 14 at 11:00AM ET.\n\n"
            "This market will resolve to \"G2 Esports\" if G2 Esports win the match "
            "against Natus Vincere.\n\n"
            "This market will resolve to \"Natus Vincere\" if Natus Vincere win the "
            "match against G2 Esports.\n\n"
            "If the match is canceled, delayed beyond 7 days, forfeited, or resolved "
            "by walkover, operator review must verify the exact Polymarket text.\n\n"
            "The resolution source for this market will be official information from "
            "https://gol.gg/esports/home."
        ),
        "outcomes": "[\"G2 Esports\", \"Natus Vincere\"]",
        "active": True,
        "closed": False,
        "sportsMarketType": "moneyline",
        "gameStartTime": "2026-05-14 15:00:00+00",
    }
    return {
        "id": "432728",
        "slug": "lol-g2-navi-2026-05-14",
        "title": "LoL: G2 Esports vs Natus Vincere (BO3) - Esports World Cup EMEA Qualifier Playoffs",
        "description": market["description"],
        "resolutionSource": "https://www.twitch.tv/ewclol2026",
        "active": True,
        "closed": False,
        "eventStartTime": "2026-05-14T15:00:00Z",
        "seriesSlug": "league-of-legends",
        "eventMetadata": {
            "league": "Esports World Cup",
            "serie": "EMEA Qualifier",
            "tournament": "Playoffs",
        },
        "teams": [{"name": "G2 Esports"}, {"name": "Natus Vincere"}],
        "tags": [
            {"id": "65", "label": "league of legends", "slug": "league-of-legends"},
            {"id": "64", "label": "Esports", "slug": "esports"},
        ],
        "markets": [market],
    }


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


def test_dry_run_performs_zero_network_calls():
    payload = discovery.build_dry_run_status()

    assert payload["status"] == "dry_run_no_network"
    assert payload["network_allowed_explicitly"] is False
    assert payload["network_calls_performed"] == 0
    assert payload["polymarket_api_calls_performed"] == 0
    assert payload["fetch_performed"] is False
    assert payload["planned_capture_status"] == "draft"
    assert payload["auto_promote_to_ready_for_local_review"] is False


def test_fetch_one_mode_is_capped_at_one_selected_market_and_writes_artifacts(tmp_path):
    event = _sample_event()
    fetcher = MockFetcher([[event], event])

    payload = discovery.run_fetch_one(write=True, fetcher=fetcher, root=tmp_path)

    assert payload["fetch_status"] == "selected"
    assert payload["selected_market_id"] == "2121194"
    assert payload["selected_market_title_or_question"] == event["markets"][0]["question"]
    assert payload["network_call_count"] == 2
    assert len(payload["endpoint_or_url_used"]) == 2
    assert all(url.startswith(discovery.GAMMA_BASE_URL) for url in fetcher.urls)

    raw = _load_json(
        tmp_path
        / "pm_bot"
        / "live_readonly"
        / "esports_market_discovery"
        / discovery.RAW_FETCH_JSON
    )
    normalized = _load_json(
        tmp_path
        / "pm_bot"
        / "live_readonly"
        / "esports_market_discovery"
        / discovery.NORMALIZED_JSON
    )
    source_capture = _load_json(
        tmp_path
        / "pm_bot"
        / "live_readonly"
        / "esports_market_discovery"
        / discovery.SOURCE_CAPTURE_JSON
    )

    assert raw["network_call_count"] == 2
    assert raw["selected_market_id"] == "2121194"
    assert normalized["market_class"] == "esports"
    assert normalized["planned_capture_status"] == "draft"
    assert normalized["auto_promote_to_ready_for_local_review"] is False
    assert source_capture["planned_source_capture_status"] == "draft"
    assert source_capture["planned_capture_status"] == "draft"
    assert source_capture["auto_fill_allowed_only_as_draft"] is True

    with pytest.raises(ValueError):
        discovery.run_fetch_one(max_markets=2, fetcher=fetcher)


def test_no_auth_headers_or_secret_env_vars_are_used():
    assert "Authorization" not in discovery.PUBLIC_HEADERS
    assert "Bearer" not in json.dumps(discovery.PUBLIC_HEADERS)

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_tokens = [
        "os.environ",
        "getenv",
        "openrouter_api_key",
        "private_key =",
        "private_key=",
        "secret_key",
        "bearer ",
        "authorization",
    ]
    for token in forbidden_tokens:
        assert token not in lowered


def test_no_wallet_order_trading_runtime_dispatcher_queue_or_browser_code_path_exists():
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
        if isinstance(node, ast.FunctionDef):
            lowered_name = node.name.lower()
            assert "wallet" not in lowered_name
            assert "trade" not in lowered_name
            assert "order" not in lowered_name
            assert "dispatcher" not in lowered_name
            assert "queue" not in lowered_name
        if isinstance(node, ast.Attribute):
            assert node.attr.lower() not in forbidden_call_names

    source = MODULE_PATH.read_text(encoding="utf-8")
    assert 'method="GET"' in source
    for token in ['method="POST"', 'method="PATCH"', 'method="DELETE"', "clob.polymarket"]:
        assert token not in source


def test_no_openrouter_call_path_exists():
    source = MODULE_PATH.read_text(encoding="utf-8").lower()

    assert "openrouter_api_key" not in source
    assert "openrouter.ai" not in source
    assert "api.openrouter" not in source


def test_result_artifacts_contain_no_market_prediction_or_side_selection_fields(tmp_path):
    event = _sample_event()
    payload = discovery.run_fetch_one(
        write=True,
        fetcher=MockFetcher([[event], event]),
        root=tmp_path,
    )
    assert payload["fetch_status"] == "selected"

    artifact_paths = [
        tmp_path / "docs" / "PMBOT_SOURCE_009A_RESULT.json",
        tmp_path
        / "pm_bot"
        / "live_readonly"
        / "esports_market_discovery"
        / discovery.NORMALIZED_JSON,
        tmp_path
        / "pm_bot"
        / "live_readonly"
        / "esports_market_discovery"
        / discovery.SOURCE_CAPTURE_JSON,
        tmp_path
        / "pm_bot"
        / "live_readonly"
        / "esports_market_discovery"
        / discovery.CHECKLIST_JSON,
    ]
    forbidden_exact = {
        "probability",
        "ev",
        "edge",
        "confidence",
        "confidence_score",
        "side_selection",
        "side-selection",
        "recommended_side",
    }
    allowed_false_safety_fields = {
        "probability_ev_edge_confidence_generated",
        "side_selection_generated",
    }
    for path in artifact_paths:
        payload = _load_json(path)
        keys = {key.lower() for key in _iter_keys(payload)}
        assert forbidden_exact.isdisjoint(keys)
        for field in allowed_false_safety_fields:
            if field in payload:
                assert payload[field] is False


def test_no_suitable_esports_market_found_exits_safe():
    non_match = {
        "id": "1",
        "slug": "not-esports",
        "title": "Generic non-match market",
        "active": True,
        "closed": False,
        "markets": [],
        "tags": [],
    }
    fetcher = MockFetcher([[non_match]])

    payload = discovery.run_fetch_one(fetcher=fetcher, max_event_pages=1)

    assert payload["status"] == "no_suitable_esports_market_found"
    assert payload["fetch_status"] == "no_suitable_esports_market_found"
    assert payload["selected_market_id"] is None
    assert payload["network_call_count"] == 1
    assert payload["operator_review_required"] is True
    assert payload["planned_capture_status"] == "draft"


def test_existing_source_007_and_008b_state_remains_preserved():
    ingest = _load_json(SOURCE_007_INGEST)
    gate = _load_json(SOURCE_007_GATE)
    source_008b = _load_json(ROOT / "docs" / "PMBOT_SOURCE_008B_RESULT.json")

    assert ingest["real_ingested_template_count"] >= source_008b["real_ingested_template_count_preserved"]
    assert gate["real_ingested_template_count"] >= source_008b["real_ingested_template_count_preserved"]
    assert gate["draft_ingested_template_count"] >= source_008b["draft_ingested_template_count_preserved"]
    assert gate["ready_ingested_template_count"] == 0
    assert gate["future_live_002_allowed"] is False
    assert source_008b["real_ingested_template_count_preserved"] == 1
    assert source_008b["draft_ingested_template_count_preserved"] == 1
    assert source_008b["ready_ingested_template_count_preserved"] == 0
    assert source_008b["future_live_002_allowed"] is False
