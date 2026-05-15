from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from pm_bot.trading_core.public_gamma_market_client import (
    PUBLIC_GAMMA_SOURCE_NAME,
    PUBLIC_GAMMA_SOURCE_TYPE,
    READ_ONLY_METHOD,
    PublicGammaFetchError,
    PublicGammaMarketClient,
)
import pm_bot.trading_core.public_market_token_discovery as discovery
import pm_bot.trading_core.public_market_token_discovery_models as discovery_models
from pm_bot.trading_core.public_market_token_discovery import (
    public_market_token_discovery_artifact_paths,
    run_public_market_token_discovery,
)
from pm_bot.trading_core.public_market_token_discovery_models import (
    DISCOVERY_STATUS_MARKETS_WITHOUT_TOKENS,
    DISCOVERY_STATUS_READY,
    DISCOVERY_STATUS_UNAVAILABLE,
    PUBLIC_MARKET_TOKEN_DISCOVERY_LATEST_STATUS_CONTRACT,
    validate_public_market_token_discovery_result,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"

NEW_071A_RUNTIME_FILES = (
    Path("pm_bot/trading_core/public_market_token_discovery_models.py"),
    Path("pm_bot/trading_core/public_market_token_discovery.py"),
    Path("pm_bot/operator_runner/public_market_token_discovery.py"),
)

FORBIDDEN_RUNTIME_STRINGS = (
    "API_SECRET",
    "PASSPHRASE",
    "POLYMARKET_PK",
    "POLYMARKET_PRIVATE_KEY",
    "POLYGON_WALLET_PRIVATE_KEY",
    "Authorization",
    "Bearer",
    "Cookie",
    "X-Api-Key",
    "createAndPostOrder",
    "OrderBuilder",
)

FORBIDDEN_CALL_PATTERNS = (
    r"\bcreate_order\s*\(",
    r"\bpost_order\s*\(",
    r"\bsubmit_order\s*\(",
    r"\bplace_order\s*\(",
    r"\bcancel_order\s*\(",
    r"\bsign_order\s*\(",
    r"\bsign_payload\s*\(",
    r"\bconnect_wallet\s*\(",
    r"\bload_wallet\s*\(",
)


class SourceBackedPublicClient(PublicGammaMarketClient):
    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(base_url="https://gamma-api.polymarket.com")
        self.payload = payload

    def search_public_markets(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "source_name": PUBLIC_GAMMA_SOURCE_NAME,
            "source_type": PUBLIC_GAMMA_SOURCE_TYPE,
            "base_url": self.base_url,
            "endpoint_path": "/events",
            "sanitized_query": {"q": "BTC", "limit": "25"},
            "data": self.payload,
            "request_evidence": {},
            "response_evidence": {},
            "network_used": True,
        }


class FailingPublicClient(PublicGammaMarketClient):
    def __init__(self) -> None:
        super().__init__(base_url="https://gamma-api.polymarket.com")

    def search_public_markets(self, **kwargs: Any) -> dict[str, Any]:
        raise PublicGammaFetchError(
            "planned public dependency failure",
            error_payload={
                "source_name": PUBLIC_GAMMA_SOURCE_NAME,
                "source_type": PUBLIC_GAMMA_SOURCE_TYPE,
                "endpoint_path": "/events",
                "sanitized_query": {"q": "BTC"},
                "error_type": "PlannedFailure",
                "message": "planned public dependency failure",
                "network_used": True,
                "generated_at": GENERATED_AT,
            },
        )


def _payload(token_ids: list[str] | None = None) -> dict[str, Any]:
    return {
        "events": [
            {
                "id": "event-btc-071a",
                "slug": "bitcoin-up-or-down-071a",
                "title": "Bitcoin public market event",
                "active": True,
                "closed": False,
                "markets": [
                    {
                        "id": "market-btc-071a",
                        "slug": "bitcoin-above-threshold-071a",
                        "question": "Will Bitcoin be above the public threshold?",
                        "active": True,
                        "closed": False,
                        "outcomes": json.dumps(["Yes", "No"]),
                        "clobTokenIds": json.dumps(token_ids if token_ids is not None else ["1001", "1002"]),
                        "tags": [{"label": "Bitcoin"}, {"label": "BTC"}],
                    }
                ],
            }
        ]
    }


def _assert_required_false_flags(value: dict[str, Any]) -> None:
    for field in (
        "private_key_read",
        "wallet_connection_attempted",
        "signing_attempted",
        "signed_payload_generated",
        "order_submission_attempted",
        "order_cancellation_attempted",
        "authenticated_request_performed",
        "allowed_for_live",
        "browser_automation_added",
        "scheduler_or_daemon_added",
        "autonomous_live_trading_added",
        "token_id_generation_enabled",
        "fake_token_ids_allowed",
    ):
        assert value[field] is False, field
    assert value["resolved_blocker_count"] == 0


def test_071a_runtime_sources_do_not_read_secret_names_or_add_forbidden_calls() -> None:
    assert READ_ONLY_METHOD == "GET"
    for path in NEW_071A_RUNTIME_FILES:
        source = path.read_text(encoding="utf-8")
        lowered = source.lower()
        for forbidden in FORBIDDEN_RUNTIME_STRINGS:
            assert forbidden.lower() not in lowered, path
        for pattern in FORBIDDEN_CALL_PATTERNS:
            assert re.search(pattern, source, re.IGNORECASE) is None, path
        assert "time.sleep(" not in source
        assert "import threading" not in source
        assert "import asyncio" not in source
        assert "daemon=True" not in source.replace(" ", "")

    runner_source = inspect.getsource(discovery)
    model_source = inspect.getsource(discovery_models)
    assert "urlopen" not in runner_source
    assert "os.environ" not in runner_source
    assert "os.environ" not in model_source


def test_source_backed_public_candidates_are_marked_and_token_ids_are_not_generated(tmp_path: Path) -> None:
    result = run_public_market_token_discovery(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        public_client=SourceBackedPublicClient(_payload()),
        local_artifact_paths=[tmp_path / "missing-local-artifact.json"],
        generated_at=GENERATED_AT,
    )

    assert result["status"] == DISCOVERY_STATUS_READY
    assert result["market_candidate_count"] == 1
    assert result["outcome_token_candidate_count"] == 2
    assert validate_public_market_token_discovery_result(result)["valid"] is True
    _assert_required_false_flags(result)
    _assert_required_false_flags(result["latest_status"])

    market_candidate = result["market_candidates"][0]
    token_candidate = result["outcome_token_candidates"][0]
    assert market_candidate["source_backed"] is True
    assert market_candidate["source_type"] == PUBLIC_GAMMA_SOURCE_TYPE
    assert token_candidate["source_backed"] is True
    assert token_candidate["token_id"] == "1001"
    assert token_candidate["token_id_is_generated"] is False
    assert token_candidate["token_id_is_fixture_or_placeholder"] is False
    assert token_candidate["source_field"] == "clobTokenIds"


def test_fake_or_fixture_token_ids_are_not_emitted(tmp_path: Path) -> None:
    result = run_public_market_token_discovery(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        public_client=SourceBackedPublicClient(_payload(["fake-btc-yes-token", "fixture-btc-no-token"])),
        local_artifact_paths=[tmp_path / "missing-local-artifact.json"],
        generated_at=GENERATED_AT,
    )

    assert result["status"] == DISCOVERY_STATUS_MARKETS_WITHOUT_TOKENS
    assert result["market_candidate_count"] == 1
    assert result["outcome_token_candidate_count"] == 0
    assert result["outcome_token_candidates"] == []
    assert validate_public_market_token_discovery_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_missing_public_dependency_fails_closed_with_discovery_unavailable(tmp_path: Path) -> None:
    result = run_public_market_token_discovery(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        public_client=FailingPublicClient(),
        local_artifact_paths=[tmp_path / "no-source-backed-local-artifact.json"],
        generated_at=GENERATED_AT,
    )

    paths = public_market_token_discovery_artifact_paths(tmp_path)
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))

    assert result["status"] == DISCOVERY_STATUS_UNAVAILABLE
    assert result["market_candidates"] == []
    assert result["outcome_token_candidates"] == []
    assert result["source_errors"]
    assert latest_status["status"] == DISCOVERY_STATUS_UNAVAILABLE
    assert latest_status["allowed_for_live"] is False
    assert validate_public_market_token_discovery_result(result)["valid"] is True


def test_source_backed_local_public_artifact_can_be_ingested_without_network(tmp_path: Path) -> None:
    artifact = tmp_path / "normalized_public_market_snapshot_054.json"
    artifact.write_text(
        json.dumps(
            {
                "contract_version": "pmbot_normalized_public_market_snapshot_054.v1",
                "source_name": "public_gamma_live_read_only",
                "source_type": "public_gamma_read_only",
                "market_symbol": "BTC",
                "selected_market": {
                    "market_id": "local-market-btc-071a",
                    "market_slug": "local-bitcoin-market-071a",
                    "question": "Will Bitcoin stay source backed?",
                    "event_id": "local-event-btc-071a",
                    "event_slug": "local-bitcoin-event-071a",
                    "active": True,
                    "closed": False,
                    "outcome_labels": ["Yes", "No"],
                    "public_market_token_ids": ["2001", "2002"],
                },
                "market_snapshot": {},
                "network_used": True,
                "generated_at": GENERATED_AT,
            }
        ),
        encoding="utf-8",
    )

    result = run_public_market_token_discovery(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "out",
        local_artifact_paths=[artifact],
        public_client=FailingPublicClient(),
        generated_at=GENERATED_AT,
    )

    assert result["status"] == DISCOVERY_STATUS_READY
    assert result["network_used"] is False
    assert result["market_candidates"][0]["source_origin"] == "local_artifact"
    assert result["market_candidates"][0]["source_type"] == "public_local_artifact_read_only"
    assert result["outcome_token_candidates"][0]["token_id"] == "2001"
    assert result["outcome_token_candidates"][0]["source_backed"] is True
    assert validate_public_market_token_discovery_result(result)["valid"] is True


def test_runner_emits_required_artifacts_on_fail_closed_path(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PMBOT_GAMMA_BASE_URL"] = "http://127.0.0.1:1"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.public_market_token_discovery",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--local-artifact",
            str(tmp_path / "missing-local-artifact.json"),
            "--artifacts-dir",
            str(tmp_path / "artifacts"),
        ],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = public_market_token_discovery_artifact_paths(tmp_path / "artifacts")

    assert completed.returncode == 0, completed.stderr
    assert "Public market token discovery completed." in completed.stdout
    assert "Live execution: blocked" in completed.stdout
    assert paths["result"].exists()
    assert paths["latest_status"].exists()
    assert paths["market_candidates"].exists()
    assert paths["outcome_token_candidates"].exists()
    assert paths["redaction_policy"].exists()
    assert paths["operator_summary"].exists()
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    assert latest_status["contract_version"] == PUBLIC_MARKET_TOKEN_DISCOVERY_LATEST_STATUS_CONTRACT
    assert latest_status["status"] == DISCOVERY_STATUS_UNAVAILABLE
    assert latest_status["allowed_for_live"] is False
