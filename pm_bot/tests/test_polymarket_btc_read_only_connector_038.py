from __future__ import annotations

import json
import socket
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.operator_ui_panel_v1 import build_operator_ui_panel_v1
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.live_canary_readiness import btc_market_readiness_blocker_categories
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.polymarket_btc_read_only_connector import (
    PRICE_STATUS_NOT_AVAILABLE,
    PolymarketBTCReadOnlyConnector,
    build_btc_market_snapshot_from_payload,
    build_default_btc_fixture_market_payload,
    build_default_btc_read_only_config,
    evaluate_btc_market_snapshot_freshness,
    fetch_public_polymarket_market_read_only,
    normalize_polymarket_btc_market_payload,
    summarize_btc_market_snapshot,
    validate_btc_read_only_config,
)
from pm_bot.trading_core.risk_limit_control_plane import (
    DECISION_ALLOW_DRY_RUN,
    DECISION_HALT,
    RiskLimitOrderIntent,
    build_default_risk_limit_policy,
    build_default_risk_limit_state,
    build_risk_control_plane_summary,
    evaluate_risk_limits_for_order_intent,
)
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_btc_connector_config,
    validate_secret_boundary_btc_connector_result,
    validate_secret_boundary_btc_evidence_item,
    validate_secret_boundary_btc_market_snapshot,
    validate_secret_boundary_btc_ui_summary,
)

GENERATED_AT = "2026-05-11T00:00:00Z"
FIXTURE_PATH = Path("pm_bot/tests/fixtures/trading_core/polymarket_btc_market_sample_038.json")

FORBIDDEN_BTC_FIELDS = (
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


def _config(**overrides: Any) -> dict[str, Any]:
    config = build_default_btc_read_only_config(generated_at=GENERATED_AT)
    config.update(overrides)
    return config


def _snapshot(
    *,
    payload: Mapping[str, Any] | None = None,
    current_time: str = GENERATED_AT,
    config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return build_btc_market_snapshot_from_payload(
        payload or _fixture_payload(),
        config or _config(),
        current_time=current_time,
        generated_at=GENERATED_AT,
    )


def _intent(**overrides: Any) -> dict[str, Any]:
    value = RiskLimitOrderIntent(
        intent_id="btc-read-only-connector-038-dry-run-intent",
        market_id="btc-one-market-demo-market",
        market_slug="btc-one-market-demo",
        market_tag="BTC",
        market_category="bitcoin",
        side_label="track_yes",
        notional_usd=1.0,
        quantity=2.0,
        limit_price=0.5,
        intent_source="unit-test",
        created_at=GENERATED_AT,
        dry_run_only=True,
        operator_intent_reference="operator-intent-packet-034",
        readiness_evidence_reference="readiness-evidence-bundle-035",
        audit_replay_reference="live-connector-audit-replay-032",
        ui_panel_reference="operator-ui-panel-v1-036",
    ).to_dict()
    value.update(overrides)
    return value


def test_default_config_is_read_only_network_disabled_and_valid() -> None:
    config = _config()

    assert config["mode"] == "read_only"
    assert config["read_only"] is True
    assert config["network_enabled"] is False
    assert config["authenticated"] is False
    assert config["order_submission_supported"] is False
    assert config["wallet_required"] is False
    assert validate_btc_read_only_config(config)["valid"] is True
    assert validate_secret_boundary_btc_connector_config(config)["valid"] is True


def test_config_validation_rejects_non_btc_and_auth_or_order_capable_fields() -> None:
    non_btc = _config(market_id="eth-market", market_slug="ethereum-demo", allowed_market_tags=["ETH"])
    authenticated = _config(authenticated=True)
    order_capable = _config(order_submission_supported=True)
    wallet_required = _config(wallet_required=True)
    with_api_key = _config(api_key="forbidden")

    assert validate_btc_read_only_config(non_btc)["valid"] is False
    assert validate_btc_read_only_config(authenticated)["valid"] is False
    assert validate_btc_read_only_config(order_capable)["valid"] is False
    assert validate_btc_read_only_config(wallet_required)["valid"] is False
    assert validate_btc_read_only_config(with_api_key)["valid"] is False


def test_fixture_payload_normalizes_and_snapshot_builds_deterministically() -> None:
    payload = _fixture_payload()
    first = normalize_polymarket_btc_market_payload(payload)
    second = normalize_polymarket_btc_market_payload(deepcopy(payload))
    snapshot_one = _snapshot(payload=payload)
    snapshot_two = _snapshot(payload=deepcopy(payload))

    assert first == second
    assert snapshot_one == snapshot_two
    assert snapshot_one["market_id"] == "btc-one-market-demo-market"
    assert snapshot_one["market_slug"] == "btc-one-market-demo"
    assert snapshot_one["is_btc_related"] is True
    assert snapshot_one["status"] == "open"
    assert snapshot_one["is_open"] is True
    assert snapshot_one["is_resolved"] is False
    assert snapshot_one["risk_control_market_data_status"] == "fresh_open_btc_market"
    assert snapshot_one["best_bid"] == 0.51
    assert snapshot_one["best_ask"] == 0.53
    assert snapshot_one["spread"] == 0.02
    assert validate_secret_boundary_btc_market_snapshot(snapshot_one)["valid"] is True


def test_resolved_market_rejected_by_default_and_marked_when_allowed() -> None:
    payload = _fixture_payload()
    payload["resolved"] = True
    payload["active"] = False

    connector = PolymarketBTCReadOnlyConnector(_config())
    rejected = connector.build_snapshot_from_fixture_payload(payload, current_time=GENERATED_AT)
    assert rejected["success"] is False
    assert rejected["status"] == "payload_rejected"
    assert "resolved" in rejected["error"]["message"]

    config = _config(require_not_resolved=False, require_open_market=False)
    snapshot = _snapshot(payload=payload, config=config)
    assert snapshot["status"] == "resolved"
    assert snapshot["risk_control_market_data_status"] == "resolved_market"


def test_stale_snapshot_is_detected() -> None:
    payload = _fixture_payload()
    snapshot = _snapshot(payload=payload, current_time="2026-05-11T00:06:00Z")
    freshness = evaluate_btc_market_snapshot_freshness(
        snapshot,
        config=_config(),
        current_time="2026-05-11T00:06:00Z",
        generated_at=GENERATED_AT,
    )

    assert freshness["stale"] is True
    assert snapshot["stale"] is True
    assert snapshot["age_seconds"] == 360
    assert snapshot["risk_control_market_data_status"] == "stale_market_data"


def test_missing_prices_are_not_invented() -> None:
    payload = _fixture_payload()
    payload.pop("bestBid", None)
    payload.pop("bestAsk", None)
    payload.pop("lastPrice", None)
    payload.pop("liquidity", None)
    for outcome in payload["outcomes"]:
        for field in ("price", "bestBid", "bestAsk", "lastPrice", "liquidity"):
            outcome.pop(field, None)

    snapshot = _snapshot(payload=payload)

    assert snapshot["best_bid"] is None
    assert snapshot["best_ask"] is None
    assert snapshot["last_price"] is None
    assert snapshot["spread"] is None
    assert snapshot["liquidity"] is None
    assert snapshot["price_status"] == PRICE_STATUS_NOT_AVAILABLE
    assert {row["price_status"] for row in snapshot["outcomes"]} == {PRICE_STATUS_NOT_AVAILABLE}


def test_malformed_payload_produces_deterministic_error() -> None:
    connector = PolymarketBTCReadOnlyConnector(_config())
    first = connector.build_snapshot_from_fixture_payload({"id": "btc-one-market-demo-market"})
    second = connector.build_snapshot_from_fixture_payload({"id": "btc-one-market-demo-market"})

    assert first == second
    assert first["success"] is False
    assert first["error"]["error_code"] == "PAYLOAD_REJECTED"


def test_network_disabled_prevents_fetch_and_fixture_loader_uses_no_network(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def blocked_socket(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    connector = PolymarketBTCReadOnlyConnector(_config())
    disabled = connector.fetch_public_market_read_only()
    loaded = connector.build_snapshot_from_fixture_loader(_fixture_payload, current_time=GENERATED_AT)

    assert disabled["status"] == "network_disabled"
    assert disabled["success"] is False
    assert disabled["network_used"] is False
    assert loaded["success"] is True
    assert loaded["network_attempted"] is False
    assert loaded["external_api_calls_performed"] is False


def test_network_capable_path_requires_operator_allowance_and_public_safe_endpoint() -> None:
    config = _config(network_enabled=True, public_endpoint_url="https://example.test/public-market")
    called = False

    def fetcher(_url: str) -> Mapping[str, Any]:
        nonlocal called
        called = True
        return _fixture_payload()

    no_allowance = fetch_public_polymarket_market_read_only(
        config,
        operator_read_only_network_allowed=False,
        fetcher=fetcher,
        generated_at=GENERATED_AT,
    )
    forbidden_endpoint = fetch_public_polymarket_market_read_only(
        _config(network_enabled=True, public_endpoint_url="https://example.test/clob/orders"),
        operator_read_only_network_allowed=True,
        fetcher=fetcher,
        generated_at=GENERATED_AT,
    )

    assert no_allowance["status"] == "operator_network_not_allowed"
    assert forbidden_endpoint["status"] == "endpoint_forbidden"
    assert called is False


def test_risk_control_accepts_fresh_btc_snapshot_for_dry_run_and_never_live() -> None:
    snapshot = _snapshot()
    state = build_default_risk_limit_state(btc_market_snapshot=snapshot, generated_at=GENERATED_AT)
    decision = evaluate_risk_limits_for_order_intent(
        _intent(),
        state=state,
        policy=build_default_risk_limit_policy(generated_at=GENERATED_AT),
        generated_at=GENERATED_AT,
    )
    summary = build_risk_control_plane_summary(
        policy=build_default_risk_limit_policy(generated_at=GENERATED_AT),
        latest_decision=decision,
        btc_market_snapshot=snapshot,
        generated_at=GENERATED_AT,
    )

    assert decision["decision_status"] == DECISION_ALLOW_DRY_RUN
    assert decision["allowed_for_dry_run"] is True
    assert decision["allowed_for_live"] is False
    assert summary["market_data_status"] == "fresh_open_btc_market"
    assert summary["allowed_for_live"] is False
    assert summary["live_connector_enabled"] is False


def test_stale_btc_snapshot_causes_halt_under_policy() -> None:
    snapshot = _snapshot(current_time="2026-05-11T00:06:00Z")
    state = build_default_risk_limit_state(btc_market_snapshot=snapshot, generated_at=GENERATED_AT)
    decision = evaluate_risk_limits_for_order_intent(
        _intent(),
        state=state,
        policy=build_default_risk_limit_policy(generated_at=GENERATED_AT),
        generated_at=GENERATED_AT,
    )

    assert decision["decision_status"] == DECISION_HALT
    assert "STALE_MARKET_DATA" in {row["code"] for row in decision["halt_reasons"]}
    assert decision["allowed_for_live"] is False


def test_operator_ui_panel_surfaces_btc_market_section() -> None:
    snapshot = _snapshot()
    panel = build_operator_ui_panel_v1(
        btc_market_snapshot=snapshot,
        btc_read_only_connector_summary=summarize_btc_market_snapshot(snapshot),
        latest_paths={"btc_market_snapshot": "btc_market_snapshot_038.json"},
        generated_at=GENERATED_AT,
    )
    section_ids = {section["section_id"] for section in panel["sections"]}

    assert "btc_market_connector" in section_ids
    assert panel["btc_market_summary"]["market_id"] == "btc-one-market-demo-market"
    assert panel["btc_market_summary"]["is_btc_related"] is True
    assert panel["btc_market_summary"]["read_only_network_enabled"] is False
    assert panel["btc_market_summary"]["execution_enabling"] is False
    assert validate_secret_boundary_btc_ui_summary(panel["btc_market_summary"])["valid"] is True


def test_paper_daily_loop_surfaces_btc_summary_passively(tmp_path: Path) -> None:
    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path)
    )
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    panel = json.loads((tmp_path / "operator_ui_panel_v1.json").read_text(encoding="utf-8"))
    snapshot = json.loads((tmp_path / "btc_market_snapshot_038.json").read_text(encoding="utf-8"))

    assert result.validation_passed is True
    assert result.btc_market_snapshot_path.endswith("btc_market_snapshot_038.json")
    assert dashboard["btc_market_snapshot_summary"]["is_btc_related"] is True
    assert dashboard["btc_read_only_connector_summary"]["network_attempted"] is False
    assert dashboard["btc_market_section_feed"]["read_only_network_enabled"] is False
    assert panel["btc_market_summary"]["risk_control_market_data_status"] == "fresh_open_btc_market"
    assert snapshot["external_api_calls_performed"] is False


def test_evidence_bundle_includes_btc_read_only_connector_item() -> None:
    snapshot = _snapshot()
    summary = summarize_btc_market_snapshot(snapshot)
    bundle = build_live_canary_readiness_evidence_bundle(btc_read_only_market_connector=summary)
    item_by_type = {row["evidence_type"]: row for row in bundle["evidence_items"]}

    assert "btc_read_only_market_connector" in item_by_type
    item = item_by_type["btc_read_only_market_connector"]
    assert item["present"] is True
    assert item["review_ready"] is True
    assert item["execution_enabling"] is False
    assert validate_secret_boundary_btc_evidence_item(item)["valid"] is True


def test_blocker_matrix_keeps_btc_categories_unresolved_and_live_disabled() -> None:
    matrix = build_live_connector_blocker_matrix()
    categories = {row["blocker_category"] for row in matrix["blockers"]}

    assert set(btc_market_readiness_blocker_categories()).issubset(categories)
    assert matrix["all_blockers_unresolved"] is True
    assert matrix["resolved_blocker_count"] == 0
    assert matrix["critical_blocker_count"] == matrix["unresolved_blocker_count"]
    assert matrix["live_execution_available"] is False


def test_secret_boundary_rejects_forbidden_fields_in_btc_payloads() -> None:
    config = _config()
    snapshot = _snapshot()
    result = PolymarketBTCReadOnlyConnector(config).build_snapshot_from_fixture_payload(
        _fixture_payload(),
        current_time=GENERATED_AT,
    )
    ui_summary = dict(snapshot["ui_summary"])
    validators = (
        (config, validate_secret_boundary_btc_connector_config),
        (snapshot, validate_secret_boundary_btc_market_snapshot),
        (result, validate_secret_boundary_btc_connector_result),
        (ui_summary, validate_secret_boundary_btc_ui_summary),
    )

    for payload, validator in validators:
        assert validator(payload)["valid"] is True
        for field in FORBIDDEN_BTC_FIELDS:
            unsafe = dict(payload)
            unsafe[field] = "<redacted>"
            validation = validator(unsafe)

            assert validation["valid"] is False
            assert f"$.{field}" in validation["forbidden_secret_field_paths"]


def test_no_order_submission_payload_or_secret_fields_exist_in_safe_outputs() -> None:
    config = _config()
    snapshot = _snapshot()
    result = PolymarketBTCReadOnlyConnector(config).build_snapshot_from_fixture_payload(
        _fixture_payload(),
        current_time=GENERATED_AT,
    )
    keys = {key for _path, key, _value in _walk([config, snapshot, result, snapshot["ui_summary"]])}

    assert {
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
    }.isdisjoint(keys)
    assert config["order_submission_supported"] is False
    assert result["real_order_placement_added"] is False
    assert result["authenticated_endpoint_added"] is False
    assert result["allowed_for_live"] is False


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
