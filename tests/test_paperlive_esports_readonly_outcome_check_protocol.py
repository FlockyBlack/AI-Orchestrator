import ast
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.paper_live import esports_readonly_outcome_check_protocol as runner  # noqa: E402


MODULE_PATH = (
    ROOT / "pm_bot" / "paper_live" / "esports_readonly_outcome_check_protocol.py"
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


def test_protocol_runner_dry_run_writes_nothing(tmp_path):
    _prepare_root(tmp_path)

    result = runner.build_dry_run(tmp_path)

    assert result["status"] == "dry_run_no_write"
    assert result["files_written"] == []
    for relative_path in runner.OUTPUT_PATHS:
        assert not (tmp_path / relative_path).exists()


def test_protocol_runner_write_creates_protocol_and_readiness_artifacts(tmp_path):
    _prepare_root(tmp_path)

    summary = runner.write_artifacts(tmp_path)

    assert summary["status"] == "completed_local"
    assert (tmp_path / runner.PROTOCOL_JSON_PATH).exists()
    assert (tmp_path / runner.PROTOCOL_MD_PATH).exists()
    assert (tmp_path / runner.READINESS_GATE_JSON_PATH).exists()
    assert (tmp_path / runner.READINESS_GATE_MD_PATH).exists()


def test_protocol_says_outcome_checked_and_known_false(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    protocol = _load_json(tmp_path / runner.PROTOCOL_JSON_PATH)

    assert protocol["outcome_checked"] is False
    assert protocol["outcome_known"] is False
    assert protocol["protocol_mode"] == "protocol_only_no_fetch"


def test_protocol_requires_explicit_network_approval(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    protocol = _load_json(tmp_path / runner.PROTOCOL_JSON_PATH)

    assert protocol["future_fetch_required"] is True
    assert protocol["explicit_network_approval_required"] is True


def test_protocol_allowlists_only_market_1987056(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    protocol = _load_json(tmp_path / runner.PROTOCOL_JSON_PATH)
    limits = protocol["future_fetch_limits"]

    assert limits["max_markets"] == 1
    assert limits["market_id_allowlist"] == ["1987056"]
    assert limits["market_class_allowlist"] == ["esports"]


def test_raw_fetch_contract_has_no_fetch_and_zero_network_calls(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    contract = _load_json(tmp_path / runner.RAW_FETCH_CONTRACT_JSON_PATH)

    assert contract["fetch_performed"] is False
    assert contract["network_call_count"] == 0
    assert contract["raw_payload"] is None
    assert contract["endpoint_or_url_used"] is None


def test_normalized_evidence_contract_has_no_decision_metric_fields(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    contract = _load_json(tmp_path / runner.NORMALIZED_EVIDENCE_CONTRACT_JSON_PATH)
    keys = {key.lower() for key in _iter_keys(contract)}
    forbidden_keys = {
        "probability",
        "ev",
        "edge",
        "confidence",
        "side_selection",
        "recommended_side",
        "recommendation",
    }

    assert forbidden_keys.isdisjoint(keys)
    assert contract["outcome_known"] is False
    assert contract["final_result_text"] is None
    assert contract["no_market_action_guidance"] is True
    assert contract["no_trading_authority"] is True


def test_source_alignment_review_contract_not_performed(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    contract = _load_json(tmp_path / runner.SOURCE_ALIGNMENT_REVIEW_CONTRACT_JSON_PATH)

    assert contract["outcome_known"] is False
    assert contract["source_alignment_review_performed"] is False


def test_source_alignment_review_contract_forbids_profit_pnl_roi_ev_edge(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    contract = _load_json(tmp_path / runner.SOURCE_ALIGNMENT_REVIEW_CONTRACT_JSON_PATH)
    forbidden = set(contract["forbidden_updates"])

    assert "profit_only_score" in forbidden
    assert "PnL" in forbidden
    assert "ROI" in forbidden
    assert "EV" in forbidden
    assert "edge" in forbidden
    assert "betting confidence" in forbidden
    assert "side selection" in forbidden


def test_readiness_gate_requires_explicit_network_approval_for_paperlive004(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    gate = _load_json(tmp_path / runner.READINESS_GATE_JSON_PATH)

    assert gate["readiness_status"] == "protocol_ready_waiting_for_explicit_network_approval"
    assert gate["future_paperlive_004_requires_explicit_network_approval"] is True
    assert gate["future_paperlive_004_allowed_without_network_approval"] is False


def test_passive_workbench_surface_exists_without_queue_runtime_dispatcher_changes(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    surface = _load_json(tmp_path / runner.WORKBENCH_SURFACE_JSON_PATH)

    assert surface["protocol_available"] is True
    assert surface["raw_fetch_contract_available"] is True
    assert surface["normalized_evidence_contract_available"] is True
    assert surface["source_alignment_review_contract_available"] is True
    assert surface["readiness_gate_available"] is True
    assert surface["queue_mutated"] is False
    assert surface["runtime_wiring_changed"] is False
    assert surface["dispatcher_changed"] is False
    assert surface["background_worker_created"] is False


def test_no_network_imports_in_protocol_runner():
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

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots


def test_no_api_secret_wallet_order_runtime_dispatcher_queue_browser_behavior(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
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
            ), path


def test_existing_paperlive002_state_preserved(tmp_path):
    _prepare_root(tmp_path)
    before = _load_json(tmp_path / runner.PAPERLIVE002_FUTURE_REQUEST_PATH)

    runner.write_artifacts(tmp_path)

    after = _load_json(tmp_path / runner.PAPERLIVE002_FUTURE_REQUEST_PATH)
    assert after == before
    assert after["outcome_checked"] is False
    assert after["simulated_trade_created"] is False
    assert after["selected_side"] is None
    assert after["stake_amount"] is None


def test_existing_source_counts_preserved(tmp_path):
    _prepare_root(tmp_path)
    runner.write_artifacts(tmp_path)

    summary = _load_json(tmp_path / runner.RUN_SUMMARY_JSON_PATH)

    assert summary["real_ingested_template_count_preserved_or_after"] >= 2
    assert summary["draft_ingested_template_count_preserved_or_after"] >= 2
    assert summary["ready_ingested_template_count_after"] == 0
    assert summary["future_live_002_allowed"] is False


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
