import ast
import json
import re
import shutil
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.paper_live import esports_controlled_readonly_outcome_fetch as runner  # noqa: E402


MODULE_PATH = (
    ROOT
    / "pm_bot"
    / "paper_live"
    / "esports_controlled_readonly_outcome_fetch.py"
)


class FakeFetcher:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def fetch(self, url, timeout_seconds=runner.DEFAULT_TIMEOUT_SECONDS):
        self.requests.append((url, timeout_seconds))
        if self.responses:
            return self.responses.pop(0)
        return runner.FetchResponse("failed", None, "", None, "unexpected fake fetch")


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


def _event_payload(outcome_available=False):
    market = {
        "id": "1987056",
        "question": runner.MARKET_TITLE,
        "slug": runner.EVENT_SLUG,
        "resolutionSource": "https://gol.gg/esports/home",
        "description": (
            "This market refers to the LoL Upper bracket final match between JD Gaming "
            "and Anyone's Legend in the Esports World Cup China Qualifier Phase 2. "
            "The resolution source for this market will be official information from "
            "https://gol.gg/esports/home."
        ),
        "outcomes": json.dumps(["JD Gaming", "Anyone's Legend"]),
        "active": not outcome_available,
        "closed": outcome_available,
        "archived": False,
        "umaResolutionStatuses": "[]",
        "eventStartTime": "2026-05-21T09:00:00Z",
        "sportsMarketType": "moneyline",
    }
    if outcome_available:
        market["resolutionStatus"] = "resolved"
        market["winningOutcome"] = "JD Gaming"
    return {
        "id": "380073",
        "slug": runner.EVENT_SLUG,
        "title": runner.MARKET_TITLE,
        "resolutionSource": "https://www.douyu.com/424559",
        "markets": [market],
    }


def _fake_fetcher(outcome_available=False):
    payload = _event_payload(outcome_available=outcome_available)
    text = json.dumps(payload)
    return FakeFetcher([runner.FetchResponse("success", 200, text, payload)])


def _write_fetch(tmp_path, outcome_available=False):
    _prepare_root(tmp_path)
    fetcher = _fake_fetcher(outcome_available=outcome_available)
    result = runner.run_fetch(write=True, fetcher=fetcher, root=tmp_path)
    return result, fetcher


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


def test_dry_run_does_not_write_fetch_artifacts(tmp_path):
    _prepare_root(tmp_path)

    result = runner.build_dry_run()

    assert result["status"] == "dry_run_no_write"
    assert result["fetch_performed"] is False
    assert result["files_written"] == []
    for relative_path in runner.OUTPUT_PATHS:
        assert not (tmp_path / relative_path).exists()


def test_fetch_mode_is_limited_to_market_id_1987056(tmp_path):
    _prepare_root(tmp_path)

    with pytest.raises(ValueError, match="1987056"):
        runner.run_fetch(market_id="1987057", fetcher=_fake_fetcher(), root=tmp_path)


def test_fetch_mode_enforces_max_one_market(tmp_path):
    _prepare_root(tmp_path)

    with pytest.raises(ValueError, match="max target markets"):
        runner.run_fetch(max_markets=2, fetcher=_fake_fetcher(), root=tmp_path)


def test_fetch_mode_enforces_network_api_call_cap(tmp_path):
    _prepare_root(tmp_path)
    fetcher = _fake_fetcher()

    result = runner.run_fetch(max_calls=0, fetcher=fetcher, root=tmp_path)

    assert result["fetch_status"] == "blocked_or_unavailable"
    assert result["total_network_call_count"] == 0
    assert fetcher.requests == []


def test_fetch_mode_does_not_use_auth_headers():
    header_names = {name.lower() for name in runner.PUBLIC_HEADERS}

    assert "authorization" not in header_names
    assert "cookie" not in header_names
    assert "x-api-key" not in header_names


def test_fetch_mode_does_not_read_env_secrets():
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] != "os"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] != "os"
        if isinstance(node, ast.Attribute):
            assert node.attr.lower() not in {"getenv", "environ"}

    lowered = source.lower()
    assert ("openrouter" + "_api_key") not in lowered
    assert ("api." + "openrouter") not in lowered
    assert "openrouter.ai" not in lowered


def test_fetch_mode_creates_raw_fetch_artifact(tmp_path):
    result, fetcher = _write_fetch(tmp_path)
    raw = _load_json(tmp_path / runner.RAW_FETCH_JSON_PATH)

    assert result["artifacts_written"] is True
    assert fetcher.requests
    assert raw["schema_version"] == "paper_live_esports_outcome_raw_fetch.v1"
    assert raw["market_id"] == "1987056"
    assert raw["fetch_performed"] is True
    assert raw["polymarket_api_calls_performed"] == 1
    assert raw["authenticated_endpoints_used"] is False
    assert raw["auth_headers_used"] is False


def test_fetch_mode_creates_normalized_outcome_evidence_artifact(tmp_path):
    _write_fetch(tmp_path)
    evidence = _load_json(tmp_path / runner.NORMALIZED_EVIDENCE_JSON_PATH)

    assert evidence["schema_version"] == "paper_live_esports_normalized_outcome_evidence.v1"
    assert evidence["market_id"] == "1987056"
    assert evidence["operator_review_required"] is True
    assert evidence["no_market_action_guidance"] is True
    assert evidence["no_trading_authority"] is True


def test_fetch_mode_creates_call_ledger(tmp_path):
    _write_fetch(tmp_path)
    ledger = _load_json(tmp_path / runner.CALL_LEDGER_JSON_PATH)

    assert ledger["schema_version"] == "paper_live_esports_outcome_fetch_call_ledger.v1"
    assert ledger["allowed_market_id"] == "1987056"
    assert ledger["total_network_call_count"] == 1
    assert ledger["polymarket_api_call_count"] == 1
    assert ledger["cap_exceeded"] is False
    assert all(call["auth_used"] is False for call in ledger["calls"])


def test_fetch_mode_creates_reconciliation_input(tmp_path):
    _write_fetch(tmp_path)
    reconciliation = _load_json(tmp_path / runner.RECONCILIATION_INPUT_JSON_PATH)

    assert reconciliation["raw_fetch_artifact_path"] == runner.RAW_FETCH_JSON_PATH
    assert (
        reconciliation["normalized_outcome_evidence_path"]
        == runner.NORMALIZED_EVIDENCE_JSON_PATH
    )
    assert reconciliation["source_alignment_review_performed"] is False
    assert reconciliation["source_quality_update_performed"] is False


def test_outcome_unavailable_has_no_inferred_winner(tmp_path):
    _write_fetch(tmp_path, outcome_available=False)
    evidence = _load_json(tmp_path / runner.NORMALIZED_EVIDENCE_JSON_PATH)

    assert evidence["outcome_known"] is False
    assert evidence["outcome_evidence_status"] == "evidence_unavailable"
    assert evidence["final_result_text"] is None
    assert evidence["selected_side"] is None


def test_outcome_available_records_evidence_only_not_recommendation(tmp_path):
    _write_fetch(tmp_path, outcome_available=True)
    evidence = _load_json(tmp_path / runner.NORMALIZED_EVIDENCE_JSON_PATH)
    surface = _load_json(tmp_path / runner.WORKBENCH_SURFACE_JSON_PATH)

    assert evidence["outcome_known"] is True
    assert evidence["outcome_evidence_status"] == "evidence_available"
    assert evidence["final_result_text"] == "JD Gaming"
    assert evidence["selected_side"] is None
    assert surface["selected_side"] is None
    assert surface["no_market_action_guidance"] is True


def test_no_simulated_trade_selected_side_stake_orders_or_wallet(tmp_path):
    _write_fetch(tmp_path)
    raw = _load_json(tmp_path / runner.RAW_FETCH_JSON_PATH)
    evidence = _load_json(tmp_path / runner.NORMALIZED_EVIDENCE_JSON_PATH)
    surface = _load_json(tmp_path / runner.WORKBENCH_SURFACE_JSON_PATH)
    summary = _load_json(tmp_path / runner.RUN_SUMMARY_JSON_PATH)

    assert raw["orders_created"] is False
    assert raw["wallet_or_private_key_accessed"] is False
    assert evidence["simulated_trade_created"] is False
    assert evidence["selected_side"] is None
    assert evidence["stake_amount"] is None
    assert evidence["orders_created"] is False
    assert evidence["wallet_or_private_key_accessed"] is False
    assert surface["simulated_trade_created"] is False
    assert surface["selected_side"] is None
    assert surface["stake_amount"] is None
    assert summary["simulated_trades_created_count"] == 0
    assert summary["orders_created_count"] == 0
    assert summary["selected_side_count"] == 0
    assert summary["stake_amount_count"] == 0


def test_source_alignment_scoring_and_ranking_not_performed(tmp_path):
    _write_fetch(tmp_path)
    evidence = _load_json(tmp_path / runner.NORMALIZED_EVIDENCE_JSON_PATH)
    reconciliation = _load_json(tmp_path / runner.RECONCILIATION_INPUT_JSON_PATH)
    summary = _load_json(tmp_path / runner.RUN_SUMMARY_JSON_PATH)

    assert evidence["source_alignment_review_performed"] is False
    assert evidence["source_scoring_performed"] is False
    assert evidence["source_ranking_updated"] is False
    assert reconciliation["source_alignment_review_performed"] is False
    assert summary["source_alignment_review_performed"] is False
    assert summary["source_scoring_performed"] is False
    assert summary["source_ranking_updated"] is False


def test_no_decision_metric_or_recommendation_fields_outside_safety_keys(tmp_path):
    _write_fetch(tmp_path)
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


def test_passive_workbench_surface_exists_without_queue_runtime_dispatcher_changes(tmp_path):
    _write_fetch(tmp_path)
    surface = _load_json(tmp_path / runner.WORKBENCH_SURFACE_JSON_PATH)

    assert surface["raw_fetch_available"] is True
    assert surface["normalized_outcome_evidence_available"] is True
    assert surface["call_ledger_available"] is True
    assert surface["reconciliation_input_available"] is True
    assert surface["queue_mutated"] is False
    assert surface["runtime_wiring_changed"] is False
    assert surface["dispatcher_changed"] is False
    assert surface["background_worker_created"] is False
    assert surface["browser_automation_used"] is False
    assert surface["canonical_packets_mutated"] is False


def test_existing_paperlive003_state_preserved(tmp_path):
    _prepare_root(tmp_path)
    before = _load_json(tmp_path / runner.PAPERLIVE003_PROTOCOL_PATH)

    runner.run_fetch(write=True, fetcher=_fake_fetcher(), root=tmp_path)

    after = _load_json(tmp_path / runner.PAPERLIVE003_PROTOCOL_PATH)
    assert after == before


def test_existing_source_counts_preserved(tmp_path):
    _write_fetch(tmp_path)
    summary = _load_json(tmp_path / runner.RUN_SUMMARY_JSON_PATH)

    assert summary["real_ingested_template_count_preserved_or_after"] >= 2
    assert summary["draft_ingested_template_count_preserved_or_after"] >= 2
    assert summary["ready_ingested_template_count_after"] == 0
    assert summary["future_live_002_allowed"] is False


def test_no_openrouter_wallet_order_runtime_dispatcher_queue_browser_behavior(tmp_path):
    _write_fetch(tmp_path)
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "webbrowser",
        "selenium",
        "playwright",
        "subprocess",
        "os",
    }
    forbidden_call_names = {
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
    assert ("api." + "openrouter") not in lowered_source
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
        assert "playwright" not in lowered_text, path
        assert "selenium" not in lowered_text, path
        if "queue" in lowered_text:
            assert "no_queue_authority" in lowered_text or "no queue" in lowered_text, path
        if "runtime" in lowered_text:
            assert "no_runtime_authority" in lowered_text or "no runtime" in lowered_text, path


def test_no_forbidden_action_language_in_new_markdown_except_safety_context(tmp_path):
    _write_fetch(tmp_path)
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
        "evidence only",
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
    _write_fetch(tmp_path)

    summary = runner.build_summary_only(tmp_path)

    assert summary["status"] == "summary_only"
    assert summary["raw_fetch_available"] is True
    assert summary["normalized_outcome_evidence_available"] is True
    assert summary["call_ledger_available"] is True
    assert summary["reconciliation_input_available"] is True
    assert summary["passive_workbench_surface_available"] is True
    assert summary["source_alignment_review_performed"] is False
    assert summary["source_scoring_performed"] is False
    assert summary["source_ranking_updated"] is False
