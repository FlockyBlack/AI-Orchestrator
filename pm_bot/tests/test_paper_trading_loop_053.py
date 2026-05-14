from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.operator_ui_panel_v1 import (
    build_operator_ui_panel_v1,
    summarize_operator_ui_panel_v1,
)
from pm_bot.operator_runner.telegram_operator_control_bot import (
    build_telegram_operator_control_summary,
)
from pm_bot.trading_core.paper_trading_loop import (
    PMBOT_ARTIFACT_DIR_ENV,
    paper_trading_loop_artifact_paths,
    render_paper_trading_loop_telegram_status,
    run_paper_trading_loop,
)
from pm_bot.trading_core.paper_trading_loop_models import (
    LATEST_STATUS_CONTRACT,
    PAPER_LOOP_ARTIFACT_CONTRACT,
    REQUIRED_FALSE_FLAGS,
)

GENERATED_AT = "2026-05-14T00:00:00Z"

AUDIT_DOC = Path(
    "docs/ORCH_PMBOT_TRADING_MVP_053_DONOR_TRADING_LOOP_RISK_AND_MOCK_CLIENT_ADAPTATION.md"
)

NEW_053_RUNTIME_FILES = (
    Path("pm_bot/trading_core/paper_trading_loop_models.py"),
    Path("pm_bot/trading_core/paper_mock_market_client.py"),
    Path("pm_bot/trading_core/paper_strategy_engine.py"),
    Path("pm_bot/trading_core/paper_execution_risk.py"),
    Path("pm_bot/trading_core/paper_order_intent_builder.py"),
    Path("pm_bot/trading_core/paper_trading_loop.py"),
    Path("pm_bot/operator_runner/paper_trading_loop.py"),
)

FORBIDDEN_RUNTIME_STRINGS = (
    "PRIVATE_KEY",
    "API_SECRET",
    "PASSPHRASE",
    "POLYMARKET_PK",
    "POLYMARKET_PRIVATE_KEY",
    "POLYGON_WALLET_PRIVATE_KEY",
    "Wallet(",
    "Signer",
    "OrderBuilder",
    "createAndPostOrder",
    "placeOrder",
    "postOrder",
    "cancelOrder",
    "sign_order",
    "signed_payload",
    "tx_hash",
    "fill_id",
    "filled_size",
    "fill_price",
    "balance",
    "pnl",
)

FORBIDDEN_ARTIFACT_KEYS = {
    "order_id",
    "client_order_id",
    "transaction_hash",
    "tx_hash",
    "fill_id",
    "fill_price",
    "filled_size",
    "balance",
    "balances",
    "pnl",
    "profit",
    "signature",
    "signed_payload",
    "signed_order",
}


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    assert value["execution_mode"] == "paper"
    assert value["review_only"] is True
    for field in REQUIRED_FALSE_FLAGS:
        assert value[field] is False
    assert value["resolved_blocker_count"] == 0
    assert value["network_used"] is False
    assert value["external_api_calls_performed"] is False
    assert value["environment_secrets_read"] is False
    assert value["secrets_read"] is False
    assert value["wallet_used"] is False
    assert value["cryptographic_signing_performed"] is False
    assert value["authenticated_endpoint_call_performed"] is False
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


def _write_fixture(path: Path, *, observed_price: float, previous_observed_price: float) -> None:
    fixture = {
        "market_symbol": "BTC",
        "market_id": "btc-paper-loop-test-market",
        "market_slug": "btc-paper-loop-test-market-053",
        "question": "Will Bitcoin close above the fixture threshold?",
        "observed_price": observed_price,
        "previous_observed_price": previous_observed_price,
        "outcomes": [
            {
                "name": "Yes",
                "price": observed_price,
                "bestBid": max(round(observed_price - 0.01, 6), 0.0),
                "bestAsk": min(round(observed_price + 0.01, 6), 1.0),
                "liquidity": 2500.0,
            },
            {
                "name": "No",
                "price": round(1.0 - observed_price, 6),
            },
        ],
        "liquidity": 2500.0,
    }
    path.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_donor_audit_exists_and_classifies_allowed_fixture_future_and_forbidden_material() -> None:
    text = AUDIT_DOC.read_text(encoding="utf-8")

    for heading in (
        "## safe_to_adapt_now",
        "## adapt_as_fixture_only",
        "## reference_only_for_future_live_enablement",
        "## forbidden_in_this_task",
    ):
        assert heading in text
    for repo in (
        "https://github.com/Polymarket/agents/tree/main/agents",
        "https://github.com/jaredzwick/polymarket-trading-bot",
        "https://github.com/MrFadiAi/Polymarket-bot",
        "https://github.com/Panca2341/polymarket-trading-bot",
        "https://github.com/aulekator/Polymarket-BTC-15-Minute-Trading-Bot",
    ):
        assert repo in text
    assert "053 adapts architecture only" in text
    assert "does not vendor, import, copy, wrap, or enable donor live execution code" in text
    assert "MarketSnapshot" in text
    assert "PaperExecutionRisk" in text
    assert "PaperOrderIntent" in text
    for forbidden in FORBIDDEN_RUNTIME_STRINGS:
        assert f"`{forbidden}`" in text


def test_cli_command_runs_and_writes_default_artifacts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(PMBOT_ARTIFACT_DIR_ENV, str(tmp_path))
    completed = subprocess.run(
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
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = paper_trading_loop_artifact_paths(tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert "Paper trading loop completed." in completed.stdout
    assert "Market: BTC" in completed.stdout
    assert "Strategy: tiny-momentum" in completed.stdout
    assert "Live execution: blocked" in completed.stdout
    assert "Risk decision: APPROVED_FOR_PAPER_INTENT" in completed.stdout
    assert paths["result"].exists()
    assert paths["operator_md"].exists()
    assert paths["latest_status"].exists()
    assert paths["market_snapshot"].exists()
    assert paths["strategy_signal"].exists()
    assert paths["risk"].exists()
    assert paths["order_intent"].exists()


def test_fixture_snapshot_to_signal_risk_paper_intent_artifacts_and_latest_status(tmp_path: Path) -> None:
    result = run_paper_trading_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = paper_trading_loop_artifact_paths(tmp_path)
    saved_result = json.loads(paths["result"].read_text(encoding="utf-8"))
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    operator_md = paths["operator_md"].read_text(encoding="utf-8")

    assert result["contract_version"] == PAPER_LOOP_ARTIFACT_CONTRACT
    assert saved_result == result
    assert result["loop_status"] == "paper_loop_completed_paper_intent_ready"
    assert result["strategy_signal"]["signal_status"] == "signal_ready_for_paper_risk_review"
    assert result["risk"]["approved_for_paper_intent"] is True
    assert result["risk"]["approved_for_live"] is False
    assert result["risk"]["live_execution_blocked"] is True
    assert result["paper_order_intent"]["paper_intent_status"] == "paper_intent_review_ready"
    assert result["paper_order_intent"]["is_execution_identifier"] is False
    assert latest_status["contract_version"] == LATEST_STATUS_CONTRACT
    assert latest_status["status"] == "paper_loop_completed_paper_intent_ready"
    assert latest_status["mode"] == "paper / review-only"
    assert latest_status["live_execution"] == "blocked"
    assert "Live execution blocked: `true`" in operator_md
    assert "Review only, no live action available." in operator_md
    _assert_required_false_flags(result)
    _assert_required_false_flags(latest_status)


def test_no_signal_path_writes_no_signal_artifact_and_latest_status(tmp_path: Path) -> None:
    fixture_path = tmp_path / "no_signal_fixture.json"
    _write_fixture(fixture_path, observed_price=0.50, previous_observed_price=0.50)

    result = run_paper_trading_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        fixture=fixture_path,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = paper_trading_loop_artifact_paths(tmp_path / "artifacts")

    assert result["loop_status"] == "paper_loop_completed_no_signal"
    assert result["strategy_signal"] is None
    assert result["no_signal"]["signal_status"] == "no_signal"
    assert result["risk"]["approved_for_paper_intent"] is False
    assert result["paper_order_intent"] is None
    assert paths["no_signal"].exists()
    assert not paths["order_intent"].exists()
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    assert latest_status["signal_status"] == "no_signal"
    assert latest_status["paper_intent_status"] == "no_paper_intent"
    assert latest_status["live_execution"] == "blocked"
    _assert_required_false_flags(result)


def test_risk_blocked_path_writes_blockers_and_no_executable_intent(tmp_path: Path) -> None:
    fixture_path = tmp_path / "risk_blocked_fixture.json"
    _write_fixture(fixture_path, observed_price=0.995, previous_observed_price=0.94)

    result = run_paper_trading_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        fixture=fixture_path,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = paper_trading_loop_artifact_paths(tmp_path / "artifacts")

    assert result["loop_status"] == "paper_loop_completed_risk_blocked"
    assert result["strategy_signal"]["has_signal"] is True
    assert result["risk"]["risk_decision"] == "BLOCKED"
    assert result["risk"]["approved_for_paper_intent"] is False
    assert result["risk"]["approved_for_live"] is False
    assert result["risk"]["live_execution_blocked"] is True
    assert result["risk"]["risk_blockers"]
    assert result["paper_order_intent"] is None
    assert not paths["order_intent"].exists()
    assert "limit_price must be between" in json.dumps(result["risk"])
    _assert_required_false_flags(result)


def test_operator_ui_and_telegram_passively_include_latest_paper_trading_loop_status(tmp_path: Path) -> None:
    result = run_paper_trading_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    status = json.loads(paper_trading_loop_artifact_paths(tmp_path)["latest_status"].read_text(encoding="utf-8"))
    panel = build_operator_ui_panel_v1(
        dashboard={"paper_trading_loop_status_summary": status},
        latest_paths={"paper_trading_loop_status": status["latest_status_path"]},
        generated_at=GENERATED_AT,
    )
    panel_summary = summarize_operator_ui_panel_v1(panel)
    telegram_summary = build_telegram_operator_control_summary(
        context={"paper_trading_loop_status_summary": status},
        generated_at=GENERATED_AT,
    )
    telegram_text = render_paper_trading_loop_telegram_status(status)
    section_ids = {section["section_id"] for section in panel["sections"]}

    assert result["latest_status"] == status
    assert "paper_trading_loop" in section_ids
    assert panel["paper_trading_loop_section_ready"] is True
    assert panel["paper_trading_loop_status_summary"]["status"] == "paper_loop_completed_paper_intent_ready"
    assert panel["paper_trading_loop_status_summary"]["live_execution"] == "blocked"
    assert panel["paper_trading_loop_status_summary"]["risk_decision"] == "APPROVED_FOR_PAPER_INTENT"
    assert panel_summary["paper_trading_loop_status"] == "paper_loop_completed_paper_intent_ready"
    assert panel_summary["paper_trading_loop_live_execution"] == "blocked"
    assert telegram_summary["paper_trading_loop_status_summary"]["status"] == "paper_loop_completed_paper_intent_ready"
    assert telegram_summary["paper_trading_loop_status_summary"]["live_execution"] == "blocked"
    assert "Paper trading loop completed." in telegram_text
    assert "Live execution: blocked" in telegram_text
    assert panel["ui_exposes_no_executable_live_action"] is True
    assert telegram_summary["no_executable_live_action"] is True


def test_artifacts_contain_no_fake_execution_identifiers_or_financial_state(tmp_path: Path) -> None:
    result = run_paper_trading_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = paper_trading_loop_artifact_paths(tmp_path)
    artifacts = [
        result,
        json.loads(paths["result"].read_text(encoding="utf-8")),
        json.loads(paths["latest_status"].read_text(encoding="utf-8")),
        json.loads(paths["market_snapshot"].read_text(encoding="utf-8")),
        json.loads(paths["strategy_signal"].read_text(encoding="utf-8")),
        json.loads(paths["risk"].read_text(encoding="utf-8")),
        json.loads(paths["order_intent"].read_text(encoding="utf-8")),
    ]

    for artifact in artifacts:
        assert _walk_key_paths(artifact) == []
    assert result["paper_order_intent"]["intent_is_not_order_submission"] is True
    assert result["paper_order_intent"]["intent_is_not_execution_result"] is True
    assert result["fake_execution_artifacts_emitted"] is False


def test_new_runtime_code_avoids_credentials_live_calls_and_autonomous_loop_primitives() -> None:
    for path in NEW_053_RUNTIME_FILES:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for forbidden in FORBIDDEN_RUNTIME_STRINGS:
            assert forbidden.lower() not in lowered, path
        assert "while " not in lowered, path
        assert "time.sleep" not in lowered, path
        assert "threading" not in lowered, path
        assert "asyncio" not in lowered, path
        assert "sched." not in lowered, path


def test_existing_052_paper_canary_drill_command_still_works(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(PMBOT_ARTIFACT_DIR_ENV, str(tmp_path))
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_canary_drill",
            "--market",
            "BTC",
            "--dry-run",
        ],
        cwd=Path.cwd(),
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Paper canary drill completed." in completed.stdout
    assert "Live execution: blocked" in completed.stdout
