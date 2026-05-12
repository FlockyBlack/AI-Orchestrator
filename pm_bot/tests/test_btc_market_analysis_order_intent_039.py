from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.operator_ui_panel_v1 import build_operator_ui_panel_v1
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.btc_market_analysis_order_intent import (
    ANALYSIS_READY_FOR_DRY_RUN_INTENT,
    BLOCKED_CLOSED_OR_RESOLVED_MARKET,
    BLOCKED_LIQUIDITY_TOO_LOW,
    BLOCKED_MISSING_REQUIRED_PRICES,
    BLOCKED_NOT_BTC_MARKET,
    BLOCKED_SPREAD_TOO_WIDE,
    BLOCKED_STALE_MARKET_DATA,
    INTENT_CANDIDATE_READY,
    build_default_btc_market_analysis_config,
    evaluate_btc_analysis_to_order_intent,
    summarize_btc_analysis_order_intent,
    validate_btc_market_analysis_config,
)
from pm_bot.trading_core.live_canary_readiness import btc_market_readiness_blocker_categories
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.polymarket_btc_read_only_connector import (
    build_btc_market_snapshot_from_payload,
    build_default_btc_read_only_config,
)
from pm_bot.trading_core.risk_limit_control_plane import (
    DECISION_ALLOW_DRY_RUN,
    DECISION_BLOCK,
    DECISION_HALT,
    RISK_LIMIT_ORDER_INTENT_CONTRACT,
    build_default_risk_limit_policy,
)
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_btc_analysis_config,
    validate_secret_boundary_btc_analysis_result,
    validate_secret_boundary_btc_analysis_ui_summary,
    validate_secret_boundary_btc_dry_run_order_intent_plan,
    validate_secret_boundary_btc_dry_run_order_intent_result,
    validate_secret_boundary_btc_evidence_item,
    validate_secret_boundary_btc_risk_decision_summary,
)

GENERATED_AT = "2026-05-11T00:00:00Z"
FIXTURE_PATH = Path("pm_bot/tests/fixtures/trading_core/polymarket_btc_market_sample_038.json")

FORBIDDEN_BTC_ANALYSIS_FIELDS = (
    "private_key",
    "mnemonic",
    "seed_phrase",
    "signature",
    "signed_order",
    "signed_payload",
    "raw_transaction",
    "auth_header",
    "bearer_token",
    "api_key",
    "access_token",
    "order_submission_payload",
    "transaction_payload",
    "authorization",
    "cookie",
    "set_cookie",
    "x_api_key",
    "clob_api_key",
    "clob_secret",
    "clob_passphrase",
)


def _fixture_payload() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _connector_config(**overrides: Any) -> dict[str, Any]:
    config = build_default_btc_read_only_config(generated_at=GENERATED_AT)
    config.update(overrides)
    return config


def _snapshot(
    *,
    payload: Mapping[str, Any] | None = None,
    current_time: str = GENERATED_AT,
    connector_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return build_btc_market_snapshot_from_payload(
        payload or _fixture_payload(),
        connector_config or _connector_config(),
        current_time=current_time,
        generated_at=GENERATED_AT,
    )


def _result(
    *,
    snapshot: Mapping[str, Any] | None = None,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return evaluate_btc_analysis_to_order_intent(
        snapshot or _snapshot(),
        policy=policy,
        latest_btc_analysis_path="btc_market_analysis_039.json",
        latest_btc_order_intent_path="btc_order_intent_dry_run_039.json",
        latest_btc_risk_decision_path="btc_risk_decision_039.json",
        generated_at=GENERATED_AT,
    )


def test_default_analysis_config_is_deterministic_and_dry_run_only() -> None:
    first = build_default_btc_market_analysis_config(generated_at=GENERATED_AT)
    second = build_default_btc_market_analysis_config(generated_at=GENERATED_AT)

    assert first == second
    assert first["mode"] == "dry_run_order_intent"
    assert first["dry_run_only"] is True
    assert first["analysis_is_not_live_recommendation"] is True
    assert first["order_intent_is_not_order_submission"] is True
    assert first["default_dry_run_notional_usd"] == 1.0
    assert validate_btc_market_analysis_config(first, generated_at=GENERATED_AT)["valid"] is True
    assert validate_secret_boundary_btc_analysis_config(first, generated_at=GENERATED_AT)["valid"] is True


def test_valid_fresh_btc_fixture_analyzes_and_creates_risk_checked_dry_run_intent() -> None:
    result = _result()
    analysis = result["analysis"]
    plan = result["order_intent_plan"]
    intent = plan["order_intent"]
    risk_summary = result["risk_decision_summary"]

    assert analysis["analysis_status"] == ANALYSIS_READY_FOR_DRY_RUN_INTENT
    assert analysis["is_btc_related"] is True
    assert analysis["market_status"] == "open"
    assert analysis["stale"] is False
    assert analysis["best_bid"] == 0.51
    assert analysis["best_ask"] == 0.53
    assert analysis["spread"] == 0.02
    assert plan["dry_run_order_intent_status"] == INTENT_CANDIDATE_READY
    assert intent["contract_version"] == RISK_LIMIT_ORDER_INTENT_CONTRACT
    assert intent["intent_source"] == "btc_market_analysis_dry_run"
    assert intent["market_tag"] == "BTC"
    assert intent["dry_run_only"] is True
    assert intent["notional_usd"] <= build_default_risk_limit_policy(generated_at=GENERATED_AT)["max_order_notional_usd"]
    assert intent["limit_price"] == 0.53
    assert risk_summary["risk_decision_status"] == DECISION_ALLOW_DRY_RUN
    assert risk_summary["allowed_for_dry_run"] is True
    assert risk_summary["allowed_for_live"] is False
    _assert_live_flags_false(result)


def test_stale_snapshot_blocks_intent_and_halts_risk_control() -> None:
    result = _result(snapshot=_snapshot(current_time="2026-05-11T00:06:00Z"))

    assert result["analysis"]["analysis_status"] == BLOCKED_STALE_MARKET_DATA
    assert result["order_intent_plan"]["order_intent"] is None
    assert result["risk_decision_summary"]["risk_decision_status"] == DECISION_HALT
    assert "STALE_MARKET_DATA" in _codes(result["risk_decision"]["halt_reasons"])


def test_closed_and_resolved_snapshots_block_intent_and_halt_risk_control() -> None:
    closed_payload = _fixture_payload()
    closed_payload["active"] = False
    closed_payload["closed"] = True
    resolved_payload = _fixture_payload()
    resolved_payload["active"] = False
    resolved_payload["resolved"] = True
    connector_config = _connector_config(require_open_market=False, require_not_resolved=False)

    closed = _result(snapshot=_snapshot(payload=closed_payload, connector_config=connector_config))
    resolved = _result(snapshot=_snapshot(payload=resolved_payload, connector_config=connector_config))

    assert closed["analysis"]["analysis_status"] == BLOCKED_CLOSED_OR_RESOLVED_MARKET
    assert resolved["analysis"]["analysis_status"] == BLOCKED_CLOSED_OR_RESOLVED_MARKET
    assert closed["risk_decision_summary"]["risk_decision_status"] == DECISION_HALT
    assert resolved["risk_decision_summary"]["risk_decision_status"] == DECISION_HALT
    assert "BTC_MARKET_CLOSED" in _codes(closed["risk_decision"]["halt_reasons"])
    assert "BTC_MARKET_RESOLVED" in _codes(resolved["risk_decision"]["halt_reasons"])


def test_non_btc_snapshot_blocks_intent_and_risk_control_blocks() -> None:
    payload = _fixture_payload()
    payload["id"] = "eth-one-market-demo-market"
    payload["slug"] = "eth-one-market-demo"
    payload["question"] = "Will Ethereum close above the demo threshold on the fixture date?"
    payload["tags"] = ["ETH", "Ethereum"]
    connector_config = _connector_config(
        market_id="eth-one-market-demo-market",
        market_slug="eth-one-market-demo",
        require_btc_tag=False,
    )
    result = _result(snapshot=_snapshot(payload=payload, connector_config=connector_config))

    assert result["analysis"]["analysis_status"] == BLOCKED_NOT_BTC_MARKET
    assert result["order_intent_plan"]["order_intent"] is None
    assert result["risk_decision_summary"]["risk_decision_status"] == DECISION_BLOCK
    assert {"MARKET_NOT_WHITELISTED", "BTC_MARKET_SNAPSHOT_NOT_BTC"} & _codes(
        result["risk_decision"]["violations"]
    )


def test_missing_prices_blocks_intent_without_inventing_price_data() -> None:
    payload = _fixture_payload()
    for field in ("bestBid", "bestAsk", "lastPrice", "liquidity"):
        payload.pop(field, None)
    for outcome in payload["outcomes"]:
        for field in ("price", "bestBid", "bestAsk", "lastPrice", "liquidity"):
            outcome.pop(field, None)
    result = _result(snapshot=_snapshot(payload=payload))

    assert result["analysis"]["analysis_status"] == BLOCKED_MISSING_REQUIRED_PRICES
    assert result["analysis"]["best_bid"] is None
    assert result["analysis"]["best_ask"] is None
    assert result["order_intent_plan"]["order_intent"] is None
    assert result["price_data_invented"] is False


def test_wide_spread_and_low_liquidity_block_intent_deterministically() -> None:
    wide_payload = _fixture_payload()
    wide_payload["bestAsk"] = 0.72
    low_liquidity_payload = _fixture_payload()
    low_liquidity_payload["liquidity"] = 50.0
    for outcome in low_liquidity_payload["outcomes"]:
        outcome["liquidity"] = 50.0

    wide = _result(snapshot=_snapshot(payload=wide_payload))
    low_liquidity = _result(snapshot=_snapshot(payload=low_liquidity_payload))

    assert wide["analysis"]["analysis_status"] == BLOCKED_SPREAD_TOO_WIDE
    assert wide["order_intent_plan"]["order_intent"] is None
    assert low_liquidity["analysis"]["analysis_status"] == BLOCKED_LIQUIDITY_TOO_LOW
    assert low_liquidity["order_intent_plan"]["order_intent"] is None


def test_over_limit_notional_blocks_in_risk_control() -> None:
    policy = build_default_risk_limit_policy(generated_at=GENERATED_AT)
    policy["max_order_notional_usd"] = 0.5
    result = _result(policy=policy)

    assert result["order_intent_plan"]["order_intent"]["notional_usd"] == 1.0
    assert result["risk_decision_summary"]["risk_decision_status"] == DECISION_BLOCK
    assert "MAX_ORDER_NOTIONAL_EXCEEDED" in _codes(result["risk_decision"]["violations"])
    assert result["risk_decision_summary"]["allowed_for_live"] is False


def test_ui_panel_surfaces_btc_analysis_order_intent_section() -> None:
    result = _result()
    matrix = build_live_connector_blocker_matrix(generated_at=GENERATED_AT)
    panel = build_operator_ui_panel_v1(
        blocker_matrix=matrix,
        btc_market_snapshot=_snapshot(),
        btc_analysis_order_intent_summary=result["summary"],
        latest_paths={
            "btc_market_analysis": "btc_market_analysis_039.json",
            "btc_order_intent_dry_run": "btc_order_intent_dry_run_039.json",
            "btc_risk_decision": "btc_risk_decision_039.json",
        },
        generated_at=GENERATED_AT,
    )
    section_ids = {section["section_id"] for section in panel["sections"]}

    assert "btc_analysis_order_intent" in section_ids
    assert panel["btc_analysis_order_intent_summary"]["btc_market_analysis_status"] == (
        ANALYSIS_READY_FOR_DRY_RUN_INTENT
    )
    assert panel["btc_analysis_order_intent_summary"]["allowed_for_dry_run"] is True
    assert panel["btc_analysis_order_intent_summary"]["allowed_for_live"] is False
    assert validate_secret_boundary_btc_analysis_ui_summary(
        panel["btc_analysis_order_intent_summary"],
        generated_at=GENERATED_AT,
    )["valid"] is True


def test_paper_daily_loop_surfaces_btc_analysis_summaries_passively(tmp_path: Path) -> None:
    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path)
    )
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    panel = json.loads((tmp_path / "operator_ui_panel_v1.json").read_text(encoding="utf-8"))

    assert result.validation_passed is True
    assert result.btc_market_analysis_path.endswith("btc_market_analysis_039.json")
    assert result.btc_order_intent_dry_run_path.endswith("btc_order_intent_dry_run_039.json")
    assert result.btc_risk_decision_path.endswith("btc_risk_decision_039.json")
    assert (tmp_path / "btc_market_analysis_039.json").exists()
    assert (tmp_path / "btc_order_intent_dry_run_039.json").exists()
    assert (tmp_path / "btc_risk_decision_039.json").exists()
    assert dashboard["btc_market_analysis_summary"]["btc_market_analysis_status"] == (
        ANALYSIS_READY_FOR_DRY_RUN_INTENT
    )
    assert dashboard["btc_order_intent_dry_run_summary"]["dry_run_order_intent_status"] == INTENT_CANDIDATE_READY
    assert dashboard["btc_risk_decision_summary"]["risk_decision_status"] == DECISION_ALLOW_DRY_RUN
    assert dashboard["btc_analysis_order_intent_section_feed"]["allowed_for_live"] is False
    assert panel["btc_analysis_order_intent_summary"]["allowed_for_dry_run"] is True
    assert panel["btc_analysis_order_intent_summary"]["allowed_for_live"] is False


def test_evidence_bundle_includes_btc_analysis_order_intent_item() -> None:
    summary = _result()["summary"]
    bundle = build_live_canary_readiness_evidence_bundle(btc_analysis_order_intent_dry_run=summary)
    item_by_type = {row["evidence_type"]: row for row in bundle["evidence_items"]}
    item = item_by_type["btc_market_analysis_to_order_intent_dry_run"]

    assert item["present"] is True
    assert item["review_ready"] is True
    assert item["execution_enabling"] is False
    assert item["analysis_ready"] is True
    assert item["order_intent_dry_run_ready"] is True
    assert item["risk_decision_linked"] is True
    assert item["allowed_for_live"] is False
    assert validate_secret_boundary_btc_evidence_item(item, generated_at=GENERATED_AT)["valid"] is True


def test_blocker_matrix_keeps_btc_analysis_order_intent_live_blockers_unresolved() -> None:
    matrix = build_live_connector_blocker_matrix(generated_at=GENERATED_AT)
    categories = {row["blocker_category"] for row in matrix["blockers"]}

    assert set(btc_market_readiness_blocker_categories()).issubset(categories)
    assert matrix["all_blockers_unresolved"] is True
    assert matrix["resolved_blocker_count"] == 0
    assert matrix["critical_blocker_count"] == matrix["unresolved_blocker_count"]
    assert matrix["live_execution_available"] is False


def test_secret_boundary_rejects_forbidden_fields_in_analysis_order_intent_payloads() -> None:
    result = _result()
    config = build_default_btc_market_analysis_config(generated_at=GENERATED_AT)
    summary = summarize_btc_analysis_order_intent(result, generated_at=GENERATED_AT)
    validators = (
        (config, validate_secret_boundary_btc_analysis_config),
        (result["analysis"], validate_secret_boundary_btc_analysis_result),
        (result["order_intent_plan"], validate_secret_boundary_btc_dry_run_order_intent_plan),
        (result, validate_secret_boundary_btc_dry_run_order_intent_result),
        (result["risk_decision_summary"], validate_secret_boundary_btc_risk_decision_summary),
        (summary, validate_secret_boundary_btc_analysis_ui_summary),
    )

    for payload, validator in validators:
        assert validator(payload, generated_at=GENERATED_AT)["valid"] is True
        for field in FORBIDDEN_BTC_ANALYSIS_FIELDS:
            unsafe = dict(payload)
            unsafe[field] = "<redacted>"
            validation = validator(unsafe, generated_at=GENERATED_AT)

            assert validation["valid"] is False
            assert f"$.{field}" in validation["forbidden_secret_field_paths"]


def test_no_executable_order_payload_fields_or_recommendation_words_in_summaries() -> None:
    result = _result()
    keys = {key for _path, key, _value in _walk(result)}
    forbidden_payload_keys = {
        "order_submission_payload",
        "transaction_payload",
        "signed_order",
        "signed_payload",
        "raw_transaction",
        "private_key",
        "mnemonic",
        "authorization",
        "cookie",
        "clob_api_key",
    }
    summary_text = json.dumps(
        {
            "result_summary": result["summary"],
            "dashboard_summary": summarize_btc_analysis_order_intent(result, generated_at=GENERATED_AT),
        },
        sort_keys=True,
    ).lower()

    assert forbidden_payload_keys.isdisjoint(keys)
    assert not re.search(r"\b(buy|sell|hold)\b", summary_text)
    assert result["real_order_placement_added"] is False
    assert result["authenticated_endpoint_added"] is False
    assert result["order_intent_is_not_order_submission"] is True


def test_same_inputs_produce_deterministic_analysis_intent_and_risk_decision() -> None:
    snapshot = _snapshot()
    first = evaluate_btc_analysis_to_order_intent(deepcopy(snapshot), generated_at=GENERATED_AT)
    second = evaluate_btc_analysis_to_order_intent(deepcopy(snapshot), generated_at=GENERATED_AT)

    assert first == second
    assert first["analysis"]["analysis_id"] == second["analysis"]["analysis_id"]
    assert first["order_intent_plan"]["intent_plan_id"] == second["order_intent_plan"]["intent_plan_id"]
    assert first["risk_decision"]["decision_id"] == second["risk_decision"]["decision_id"]


def _assert_live_flags_false(value: Mapping[str, Any]) -> None:
    for field in (
        "allowed_for_live",
        "canary_executable_now",
        "live_execution_approved",
        "real_execution_available",
        "live_connector_enabled",
    ):
        assert value.get(field) is False
    assert value["risk_decision_summary"]["allowed_for_live"] is False
    assert value["risk_decision_summary"]["canary_executable_now"] is False
    assert value["risk_decision_summary"]["live_execution_approved"] is False
    assert value["risk_decision_summary"]["real_execution_available"] is False
    assert value["risk_decision_summary"]["live_connector_enabled"] is False
    assert value["risk_decision"]["allowed_for_live"] is False
    assert value["risk_decision"]["canary_executable_now"] is False
    assert value["risk_decision"]["live_execution_approved"] is False
    assert value["risk_decision"]["real_execution_available"] is False
    assert value["risk_decision"]["live_connector_enabled"] is False


def _codes(rows: list[dict[str, Any]]) -> set[str]:
    return {row["code"] for row in rows}


def _walk(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            rows.append((path, str(key), nested))
            rows.extend(_walk(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk(nested, f"{path}[{index}]"))
    return rows
