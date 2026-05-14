from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.operator_ui_panel_v1 import (
    build_operator_ui_panel_v1,
    summarize_operator_ui_panel_v1,
)
from pm_bot.operator_runner.public_market_paper_loop import (
    LATEST_PUBLIC_MARKET_PAPER_STATUS_CONTRACT,
    public_market_paper_loop_artifact_paths,
    run_public_market_paper_loop,
)
from pm_bot.operator_runner.telegram_operator_control_bot import build_telegram_operator_control_summary
from pm_bot.trading_core.paper_trading_loop import PMBOT_ARTIFACT_DIR_ENV
from pm_bot.trading_core.paper_trading_loop_models import MARKET_SNAPSHOT_CONTRACT
from pm_bot.trading_core.public_gamma_market_client import (
    READ_ONLY_METHOD,
    PublicGammaFetchError,
    PublicGammaMarketClient,
    build_default_public_gamma_fixture,
)
import pm_bot.trading_core.public_gamma_market_client as public_gamma_market_client
from pm_bot.trading_core.public_market_evidence_models import (
    FIXTURE_FALLBACK_SOURCE_TYPE,
    PUBLIC_GAMMA_SOURCE_NAME,
    PUBLIC_GAMMA_SOURCE_TYPE,
    REQUIRED_FALSE_FLAGS,
    validate_public_market_evidence_pack,
)
from pm_bot.trading_core.public_market_normalizer import normalize_public_market_result

GENERATED_AT = "2026-05-14T00:00:00Z"

NEW_054_RUNTIME_FILES = (
    Path("pm_bot/trading_core/public_gamma_market_client.py"),
    Path("pm_bot/trading_core/public_market_evidence_models.py"),
    Path("pm_bot/trading_core/public_market_normalizer.py"),
    Path("pm_bot/operator_runner/public_market_paper_loop.py"),
)

FORBIDDEN_RUNTIME_STRINGS = (
    "PRIVATE_KEY",
    "API_SECRET",
    "PASSPHRASE",
    "POLYMARKET_PK",
    "POLYMARKET_PRIVATE_KEY",
    "POLYGON_WALLET_PRIVATE_KEY",
    "Authorization",
    "Bearer",
    "Wallet(",
    "Signer",
    "OrderBuilder",
    "createAndPostOrder",
    "placeOrder",
    "postOrder",
    "cancelOrder",
    "sign_order",
    "signed_" + "payload",
    "tx_" + "hash",
    "fill_" + "id",
    "filled_" + "size",
    "fill_" + "price",
    "bal" + "ance",
    "p" + "nl",
)

FORBIDDEN_ARTIFACT_KEYS = {
    "order_" + "id",
    "client_" + "order_" + "id",
    "transaction_" + "hash",
    "tx_" + "hash",
    "fill_" + "id",
    "fill_" + "price",
    "filled_" + "size",
    "bal" + "ance",
    "bal" + "ances",
    "p" + "nl",
    "pro" + "fit",
    "signature",
    "signed_" + "payload",
    "signed_" + "order",
}


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    assert value["execution_mode"] == "paper"
    assert value["review_only"] is True
    for field in REQUIRED_FALSE_FLAGS:
        assert value[field] is False
    assert value["resolved_blocker_count"] == 0
    assert value["auth_used"] is False
    assert value["credentials_used"] is False
    assert value["wallet_used"] is False
    assert value["signing_used"] is False
    assert value["order_endpoint_used"] is False
    assert value["real_order_submitted"] is False


def _walk_key_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text.lower() in FORBIDDEN_ARTIFACT_KEYS:
                paths.append(nested_path)
            paths.extend(_walk_key_paths(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(_walk_key_paths(nested, f"{path}[{index}]"))
    return paths


def _fixture_payload(*, observed_price: float = 0.52, previous_price: float = 0.49) -> dict[str, Any]:
    payload = build_default_public_gamma_fixture(market="BTC", generated_at=GENERATED_AT)
    market = payload["events"][0]["markets"][0]
    market["outcomePrices"] = json.dumps([observed_price, round(1.0 - observed_price, 6)])
    market["previousObservedPrice"] = previous_price
    return payload


class FailingPublicClient(PublicGammaMarketClient):
    def search_public_markets(self, **kwargs: Any) -> dict[str, Any]:
        raise PublicGammaFetchError(
            "planned public fetch failure",
            error_payload={
                "source_name": PUBLIC_GAMMA_SOURCE_NAME,
                "source_type": PUBLIC_GAMMA_SOURCE_TYPE,
                "base_url": self.base_url,
                "endpoint_path": "/events",
                "sanitized_query": {"limit": "20"},
                "request_method": READ_ONLY_METHOD,
                "network_used": True,
                "error_type": "PlannedFailure",
                "message": "planned public fetch failure",
                "generated_at": GENERATED_AT,
            },
        )


def test_public_gamma_client_is_get_only_read_only_and_exposes_no_live_methods() -> None:
    client_source = inspect.getsource(PublicGammaMarketClient)
    module_source = inspect.getsource(public_gamma_market_client)
    method_names = {name for name in dir(PublicGammaMarketClient) if not name.startswith("_")}

    assert READ_ONLY_METHOD == "GET"
    assert {"fetch_active_events", "fetch_markets", "search_public_markets", "load_fixture_fallback"}.issubset(
        method_names
    )
    for forbidden in ("place_order", "cancel_order", "post_order", "create_order", "get_positions"):
        assert forbidden not in method_names
    assert "method=READ_ONLY_METHOD" in client_source
    assert "User-Agent" in module_source
    for forbidden_header in ("Authorization", "Bearer", "Cookie", "X-Api-Key"):
        assert forbidden_header not in module_source
    assert "PMBOT_GAMMA_BASE_URL" in client_source
    for forbidden_env in ("API_KEY", "ACCESS_TOKEN", "CLIENT_SECRET", "PRIVATE_KEY"):
        assert forbidden_env not in client_source


def test_new_runtime_modules_avoid_forbidden_live_strings_and_loop_primitives() -> None:
    for path in NEW_054_RUNTIME_FILES:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for forbidden in FORBIDDEN_RUNTIME_STRINGS:
            assert forbidden.lower() not in lowered, path
        assert "while " not in lowered, path
        assert "time.sleep" not in lowered, path
        assert "threading" not in lowered, path
        assert "asyncio" not in lowered, path
        assert "sched." not in lowered, path


def test_fixture_fallback_and_normalizer_produce_053_market_snapshot() -> None:
    client = PublicGammaMarketClient(base_url="https://gamma-api.polymarket.com")
    fetch_result = client.load_fixture_fallback(market="BTC", generated_at=GENERATED_AT)
    normalized = normalize_public_market_result(fetch_result, market="BTC", generated_at=GENERATED_AT)
    snapshot = normalized["market_snapshot"]

    assert fetch_result["source_type"] == FIXTURE_FALLBACK_SOURCE_TYPE
    assert fetch_result["network_used"] is False
    assert normalized["source_type"] == FIXTURE_FALLBACK_SOURCE_TYPE
    assert snapshot["contract_version"] == MARKET_SNAPSHOT_CONTRACT
    assert snapshot["market_symbol"] == "BTC"
    assert snapshot["observed_price"] == 0.52
    assert snapshot["previous_observed_price"] == 0.49
    assert snapshot["primary_outcome"] == "Yes"
    assert snapshot["token_ids_are_market_metadata_only"] is True


def test_offline_fixture_only_public_loop_writes_evidence_status_and_paper_intent(tmp_path: Path) -> None:
    result = run_public_market_paper_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        offline_fixture_only=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = public_market_paper_loop_artifact_paths(tmp_path)
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    evidence_pack = json.loads(paths["evidence_pack"].read_text(encoding="utf-8"))
    operator_md = paths["operator_md"].read_text(encoding="utf-8")

    assert result["source"] == "fixture_fallback"
    assert result["paper_order_intent"]["paper_intent_status"] == "paper_intent_review_ready"
    assert latest_status["contract_version"] == LATEST_PUBLIC_MARKET_PAPER_STATUS_CONTRACT
    assert latest_status["source"] == "fixture_fallback"
    assert latest_status["mode"] == "paper / review-only"
    assert latest_status["live_execution"] == "blocked"
    assert latest_status["evidence_pack_path"] == paths["evidence_pack"].as_posix()
    assert evidence_pack["request_method"] == "GET"
    assert evidence_pack["network_used"] is False
    assert validate_public_market_evidence_pack(evidence_pack)["valid"] is True
    assert paths["request_evidence"].exists()
    assert paths["response_evidence"].exists()
    assert paths["normalized_snapshot"].exists()
    assert paths["strategy_signal"].exists()
    assert paths["risk"].exists()
    assert paths["order_intent"].exists()
    assert not paths["no_signal"].exists()
    for snippet in (
        "live execution blocked",
        "auth_used=false",
        "credentials_used=false",
        "wallet_used=false",
        "signing_used=false",
        "order_endpoint_used=false",
    ):
        assert snippet in operator_md
    _assert_required_false_flags(result)
    _assert_required_false_flags(latest_status)
    _assert_required_false_flags(evidence_pack)


def test_public_loop_fixture_fallback_after_fetch_failure_writes_fetch_error(tmp_path: Path) -> None:
    result = run_public_market_paper_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        fixture_fallback=True,
        artifact_dir=tmp_path,
        public_client=FailingPublicClient(base_url="https://gamma-api.polymarket.com"),
        generated_at=GENERATED_AT,
    )
    paths = public_market_paper_loop_artifact_paths(tmp_path)
    fetch_error = json.loads(paths["fetch_error"].read_text(encoding="utf-8"))

    assert result["source"] == "fixture_fallback"
    assert fetch_error["status"] == "public_gamma_fetch_failed"
    assert fetch_error["network_used"] is True
    assert fetch_error["auth_used"] is False
    assert paths["result"].exists()
    assert paths["latest_status"].exists()


def test_cli_offline_fixture_only_runs_and_writes_expected_artifacts(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.public_market_paper_loop",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--offline-fixture-only",
            "--artifacts-dir",
            str(tmp_path),
        ],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = public_market_paper_loop_artifact_paths(tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert "Public market paper loop completed." in completed.stdout
    assert "Source: fixture_fallback" in completed.stdout
    assert "Live execution: blocked" in completed.stdout
    assert paths["result"].exists()
    assert paths["latest_status"].exists()
    assert paths["evidence_pack"].exists()
    assert paths["order_intent"].exists()


def test_cli_fixture_fallback_after_public_fetch_failure_writes_expected_artifacts(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PMBOT_GAMMA_BASE_URL"] = "http://127.0.0.1:1"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.public_market_paper_loop",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--fixture-fallback",
            "--artifacts-dir",
            str(tmp_path),
        ],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = public_market_paper_loop_artifact_paths(tmp_path)
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert latest_status["source"] == "fixture_fallback"
    assert paths["fetch_error"].exists()
    assert paths["evidence_pack"].exists()
    assert paths["order_intent"].exists()


def test_no_signal_path_writes_no_signal_artifact_and_no_order_intent(tmp_path: Path) -> None:
    result = run_public_market_paper_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        offline_fixture_only=True,
        fixture_payload=_fixture_payload(observed_price=0.50, previous_price=0.50),
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = public_market_paper_loop_artifact_paths(tmp_path)

    assert result["paper_order_intent"] is None
    assert result["no_signal"]["signal_status"] == "no_signal"
    assert paths["strategy_signal"].exists()
    assert paths["no_signal"].exists()
    assert not paths["order_intent"].exists()
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    assert latest_status["paper_intent_status"] == "no_paper_intent"
    assert latest_status["live_execution"] == "blocked"


def test_risk_blocked_path_writes_blockers_and_no_executable_live_intent(tmp_path: Path) -> None:
    result = run_public_market_paper_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        offline_fixture_only=True,
        fixture_payload=_fixture_payload(observed_price=0.995, previous_price=0.94),
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = public_market_paper_loop_artifact_paths(tmp_path)

    assert result["strategy_signal"]["has_signal"] is True
    assert result["risk"]["risk_decision"] == "BLOCKED"
    assert result["risk"]["risk_blockers"]
    assert result["paper_order_intent"] is None
    assert not paths["order_intent"].exists()
    assert result["real_execution_available"] is False
    assert result["order_submission_enabled"] is False
    _assert_required_false_flags(result)


def test_ui_and_telegram_passively_include_public_market_paper_status(tmp_path: Path) -> None:
    result = run_public_market_paper_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        offline_fixture_only=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    status = result["latest_status"]
    panel = build_operator_ui_panel_v1(
        dashboard={"public_market_paper_loop_status_summary": status},
        latest_paths={"public_market_paper_loop_status": status["latest_status_path"]},
        generated_at=GENERATED_AT,
    )
    panel_summary = summarize_operator_ui_panel_v1(panel)
    telegram_summary = build_telegram_operator_control_summary(
        context={"public_market_paper_loop_status_summary": status},
        generated_at=GENERATED_AT,
    )

    assert panel["public_market_paper_loop_section_ready"] is True
    assert panel["public_market_paper_loop_status_summary"]["source"] == "fixture_fallback"
    assert panel["public_market_paper_loop_status_summary"]["evidence_pack_path"] == status["evidence_pack_path"]
    assert panel["public_market_paper_loop_status_summary"]["live_execution"] == "blocked"
    assert panel["public_market_paper_loop_status_summary"]["order_submission_enabled"] is False
    assert panel_summary["public_market_paper_loop_source"] == "fixture_fallback"
    assert telegram_summary["public_market_paper_loop_status_summary"]["source"] == "fixture_fallback"
    assert telegram_summary["public_market_paper_loop_status_summary"]["live_execution"] == "blocked"
    assert telegram_summary["no_executable_live_action"] is True


def test_public_loop_artifacts_have_no_fake_execution_identifiers_or_financial_state(tmp_path: Path) -> None:
    result = run_public_market_paper_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        offline_fixture_only=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = public_market_paper_loop_artifact_paths(tmp_path)
    artifacts = [
        result,
        json.loads(paths["result"].read_text(encoding="utf-8")),
        json.loads(paths["latest_status"].read_text(encoding="utf-8")),
        json.loads(paths["evidence_pack"].read_text(encoding="utf-8")),
        json.loads(paths["normalized_snapshot"].read_text(encoding="utf-8")),
        json.loads(paths["risk"].read_text(encoding="utf-8")),
        json.loads(paths["order_intent"].read_text(encoding="utf-8")),
    ]

    for artifact in artifacts:
        assert _walk_key_paths(artifact) == []
    assert result["paper_order_intent"]["intent_is_not_order_submission"] is True
    assert result["paper_loop_result"]["fake_execution_artifacts_emitted"] is False


def test_existing_052_and_053_commands_still_work(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(PMBOT_ARTIFACT_DIR_ENV, str(tmp_path))
    env = os.environ.copy()
    canary = subprocess.run(
        [sys.executable, "-m", "pm_bot.operator_runner.paper_canary_drill", "--market", "BTC", "--dry-run"],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paper_loop = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_trading_loop",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
        ],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert canary.returncode == 0, canary.stderr
    assert paper_loop.returncode == 0, paper_loop.stderr
    assert "Paper canary drill completed." in canary.stdout
    assert "Paper trading loop completed." in paper_loop.stdout
    assert "Live execution: blocked" in canary.stdout
    assert "Live execution: blocked" in paper_loop.stdout


def test_public_loop_does_not_mutate_input_fixture_payload(tmp_path: Path) -> None:
    payload = _fixture_payload()
    before = deepcopy(payload)
    run_public_market_paper_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        offline_fixture_only=True,
        fixture_payload=payload,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )

    assert payload == before
