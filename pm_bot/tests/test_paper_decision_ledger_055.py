from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.operator_ui_panel_v1 import build_operator_ui_panel_v1, summarize_operator_ui_panel_v1
from pm_bot.operator_runner.public_market_paper_loop import run_public_market_paper_loop
from pm_bot.operator_runner.telegram_operator_control_bot import build_telegram_operator_control_summary
from pm_bot.trading_core.paper_decision_ledger import (
    SOURCE_LATEST,
    paper_decision_ledger_artifact_paths,
    run_paper_decision_ledger,
)
from pm_bot.trading_core.paper_decision_ledger_models import (
    OUTCOME_INCOMPLETE_ARTIFACTS,
    OUTCOME_NO_SIGNAL,
    OUTCOME_PAPER_INTENT_REVIEW_READY,
    OUTCOME_RISK_BLOCKED,
    RUN_SOURCE_PAPER_LOOP_053,
    RUN_SOURCE_PUBLIC_MARKET_LOOP_054,
)
from pm_bot.trading_core.paper_trading_loop import run_paper_trading_loop
from pm_bot.trading_core.public_gamma_market_client import build_default_public_gamma_fixture

GENERATED_AT = "2026-05-14T00:00:00Z"

NEW_055_RUNTIME_FILES = (
    Path("pm_bot/trading_core/paper_decision_ledger_models.py"),
    Path("pm_bot/trading_core/paper_decision_ledger.py"),
    Path("pm_bot/operator_runner/paper_decision_ledger.py"),
)

FORBIDDEN_ARTIFACT_KEYS = {
    "order_" + "id",
    "client_" + "order_" + "id",
    "tx_" + "hash",
    "fill_" + "id",
    "fill_" + "price",
    "filled_" + "size",
    "execution_" + "price",
    "execution_" + "status",
    "bal" + "ance",
    "p" + "nl",
    "pro" + "fit",
    "los" + "s",
    "realized_" + "pnl",
    "unrealized_" + "pnl",
    "position_" + "opened",
    "position_" + "closed",
}


def test_ledger_command_runs_from_latest_054_artifacts(tmp_path: Path) -> None:
    run_public_market_paper_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        offline_fixture_only=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_decision_ledger",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path),
            "--source",
            SOURCE_LATEST,
            "--json",
            "--reset-for-test",
        ],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    status = json.loads(completed.stdout)

    assert completed.returncode == 0, completed.stderr
    assert status["latest_run_source"] == RUN_SOURCE_PUBLIC_MARKET_LOOP_054
    assert status["last_outcome"] == OUTCOME_PAPER_INTENT_REVIEW_READY
    assert status["ledger_entry_count"] == 1
    assert status["live_execution_blocked"] is True
    assert paper_decision_ledger_artifact_paths(tmp_path)["ledger"].exists()


def test_ledger_command_works_with_latest_053_fixture_artifacts(tmp_path: Path) -> None:
    run_paper_trading_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_decision_ledger",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path),
            "--source",
            SOURCE_LATEST,
            "--json",
            "--reset-for-test",
        ],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    status = json.loads(completed.stdout)

    assert completed.returncode == 0, completed.stderr
    assert status["latest_run_source"] == RUN_SOURCE_PAPER_LOOP_053
    assert status["last_outcome"] == OUTCOME_PAPER_INTENT_REVIEW_READY
    assert status["source_type"]


def test_no_signal_public_market_054_outcome_is_recorded(tmp_path: Path) -> None:
    run_public_market_paper_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        offline_fixture_only=True,
        fixture_payload=_public_fixture(observed_price=0.50, previous_price=0.50),
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    result = run_paper_decision_ledger(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        source=SOURCE_LATEST,
        reset_for_test=True,
        generated_at=GENERATED_AT,
    )
    entry = result["ledger_entry"]

    assert entry["run_source"] == RUN_SOURCE_PUBLIC_MARKET_LOOP_054
    assert entry["outcome"] == OUTCOME_NO_SIGNAL
    assert entry["no_signal_path"].endswith("public_market_no_signal_054.json")
    assert result["summary"]["count_by_outcome"][OUTCOME_NO_SIGNAL] == 1


def test_paper_intent_review_ready_fixture_outcome_is_recorded(tmp_path: Path) -> None:
    run_paper_trading_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    result = run_paper_decision_ledger(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        source=RUN_SOURCE_PAPER_LOOP_053,
        reset_for_test=True,
        generated_at=GENERATED_AT,
    )
    entry = result["ledger_entry"]

    assert entry["run_source"] == RUN_SOURCE_PAPER_LOOP_053
    assert entry["outcome"] == OUTCOME_PAPER_INTENT_REVIEW_READY
    assert entry["paper_intent_path"].endswith("paper_trading_order_intent_053.json")
    assert entry["ledger_entry_id_semantics"].startswith("internal review ledger identifier only")
    assert "not an order id" in entry["ledger_entry_id_semantics"]


def test_risk_blocked_outcome_is_recorded(tmp_path: Path) -> None:
    fixture = tmp_path / "risk_blocked_fixture.json"
    _write_fixture(fixture, observed_price=0.995, previous_observed_price=0.94)
    run_paper_trading_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        fixture=fixture,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    result = run_paper_decision_ledger(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        source=RUN_SOURCE_PAPER_LOOP_053,
        reset_for_test=True,
        generated_at=GENERATED_AT,
    )

    assert result["ledger_entry"]["outcome"] == OUTCOME_RISK_BLOCKED
    assert result["ledger_entry"]["risk_decision"] == "BLOCKED"
    assert result["ledger_entry"]["risk_blockers"]
    assert result["ledger_entry"]["paper_intent_path"] == ""


def test_incomplete_artifacts_path_writes_incomplete_report(tmp_path: Path) -> None:
    result = run_paper_decision_ledger(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        source=RUN_SOURCE_PUBLIC_MARKET_LOOP_054,
        reset_for_test=True,
        generated_at=GENERATED_AT,
    )
    paths = paper_decision_ledger_artifact_paths(tmp_path)
    incomplete = json.loads(paths["incomplete_artifacts"].read_text(encoding="utf-8"))

    assert result["ledger_entry"]["outcome"] == OUTCOME_INCOMPLETE_ARTIFACTS
    assert incomplete["status"] == OUTCOME_INCOMPLETE_ARTIFACTS
    assert incomplete["missing_artifacts"]
    assert paths["ledger"].exists()


def test_append_only_ledger_behavior_and_latest_status_are_written(tmp_path: Path) -> None:
    run_paper_trading_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    first = run_paper_decision_ledger(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        source=RUN_SOURCE_PAPER_LOOP_053,
        reset_for_test=True,
        generated_at=GENERATED_AT,
    )
    first_entry = dict(first["ledger"]["entries"][0])
    second = run_paper_decision_ledger(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        source=RUN_SOURCE_PAPER_LOOP_053,
        generated_at=GENERATED_AT,
    )
    paths = paper_decision_ledger_artifact_paths(tmp_path)
    ledger = json.loads(paths["ledger"].read_text(encoding="utf-8"))
    status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))

    assert ledger["entry_count"] == 2
    assert ledger["entries"][0] == first_entry
    assert second["ledger_entry"]["ledger_entry_id"] != first_entry["ledger_entry_id"]
    assert status["ledger_entry_count"] == 2
    assert status["count_by_outcome"][OUTCOME_PAPER_INTENT_REVIEW_READY] == 2


def test_operator_markdown_includes_live_blocked_and_review_only_next_action(tmp_path: Path) -> None:
    run_paper_trading_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    run_paper_decision_ledger(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        source=RUN_SOURCE_PAPER_LOOP_053,
        reset_for_test=True,
        generated_at=GENERATED_AT,
    )
    operator_md = paper_decision_ledger_artifact_paths(tmp_path)["operator_md"].read_text(encoding="utf-8")

    assert "live execution blocked" in operator_md
    assert "review-only next action" in operator_md
    assert "Ledger entry count" in operator_md


def test_ui_and_telegram_passive_summaries_include_latest_ledger_status(tmp_path: Path) -> None:
    run_paper_trading_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    result = run_paper_decision_ledger(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        source=RUN_SOURCE_PAPER_LOOP_053,
        reset_for_test=True,
        generated_at=GENERATED_AT,
    )
    status = result["latest_status"]
    panel = build_operator_ui_panel_v1(
        dashboard={"paper_decision_ledger_status_summary": status},
        latest_paths={"paper_decision_ledger_status": status["latest_ledger_path"]},
        generated_at=GENERATED_AT,
    )
    panel_summary = summarize_operator_ui_panel_v1(panel)
    telegram_summary = build_telegram_operator_control_summary(
        context={"paper_decision_ledger_status_summary": status},
        generated_at=GENERATED_AT,
    )
    section_ids = {section["section_id"] for section in panel["sections"]}

    assert "paper_decision_ledger" in section_ids
    assert panel["paper_decision_ledger_section_ready"] is True
    assert panel["paper_decision_ledger_status_summary"]["last_outcome"] == OUTCOME_PAPER_INTENT_REVIEW_READY
    assert panel["paper_decision_ledger_status_summary"]["ledger_entry_count"] == 1
    assert panel["paper_decision_ledger_status_summary"]["live_execution_blocked"] is True
    assert panel_summary["paper_decision_ledger_last_outcome"] == OUTCOME_PAPER_INTENT_REVIEW_READY
    assert telegram_summary["paper_decision_ledger_status_summary"]["last_outcome"] == OUTCOME_PAPER_INTENT_REVIEW_READY
    assert telegram_summary["paper_decision_ledger_status_summary"]["ledger_entry_count"] == 1
    assert telegram_summary["no_executable_live_action"] is True


def test_no_fake_execution_or_financial_state_fields_are_generated(tmp_path: Path) -> None:
    run_paper_trading_loop(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    result = run_paper_decision_ledger(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        source=RUN_SOURCE_PAPER_LOOP_053,
        reset_for_test=True,
        generated_at=GENERATED_AT,
    )
    paths = paper_decision_ledger_artifact_paths(tmp_path)
    artifacts = [
        result["ledger_entry"],
        json.loads(paths["ledger"].read_text(encoding="utf-8")),
        json.loads(paths["latest_status"].read_text(encoding="utf-8")),
        json.loads(paths["summary"].read_text(encoding="utf-8")),
        json.loads(paths["trace"].read_text(encoding="utf-8")),
    ]

    for artifact in artifacts:
        assert _walk_forbidden_key_paths(artifact) == []
    assert result["ledger_entry"]["live_execution_blocked"] is True
    assert result["ledger_entry"]["review_only"] is True


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    for path in NEW_055_RUNTIME_FILES:
        text = path.read_text(encoding="utf-8").lower()
        assert "while " not in text, path
        assert "time.sleep" not in text, path
        assert "threading" not in text, path
        assert "asyncio" not in text, path
        assert "sched." not in text, path


def test_existing_052_053_054_commands_still_work(tmp_path: Path) -> None:
    commands = [
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_canary_drill",
            "--market",
            "BTC",
            "--dry-run",
            "--artifact-dir",
            str(tmp_path / "canary"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_trading_loop",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "paper_loop"),
        ],
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
            str(tmp_path / "public_loop"),
        ],
    ]

    completed = [
        subprocess.run(
            command,
            cwd=Path.cwd(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        for command in commands
    ]

    assert completed[0].returncode == 0, completed[0].stderr
    assert completed[1].returncode == 0, completed[1].stderr
    assert completed[2].returncode == 0, completed[2].stderr
    assert "Paper canary drill completed." in completed[0].stdout
    assert "Paper trading loop completed." in completed[1].stdout
    assert "Public market paper loop completed." in completed[2].stdout
    assert all("Live execution: blocked" in result.stdout for result in completed)


def _public_fixture(*, observed_price: float, previous_price: float) -> dict[str, Any]:
    payload = build_default_public_gamma_fixture(market="BTC", generated_at=GENERATED_AT)
    market = payload["events"][0]["markets"][0]
    market["outcomePrices"] = json.dumps([observed_price, round(1.0 - observed_price, 6)])
    market["previousObservedPrice"] = previous_price
    return payload


def _write_fixture(path: Path, *, observed_price: float, previous_observed_price: float) -> None:
    fixture = {
        "market_symbol": "BTC",
        "market_id": "btc-paper-decision-ledger-test-market",
        "market_slug": "btc-paper-decision-ledger-test-market-055",
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


def _walk_forbidden_key_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text.lower() in FORBIDDEN_ARTIFACT_KEYS:
                paths.append(nested_path)
            paths.extend(_walk_forbidden_key_paths(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(_walk_forbidden_key_paths(nested, f"{path}[{index}]"))
    return paths
