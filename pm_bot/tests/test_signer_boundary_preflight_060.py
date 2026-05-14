from __future__ import annotations

import inspect
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
import pm_bot.operator_runner.signer_boundary_preflight as signer_boundary_runner
from pm_bot.operator_runner.telegram_operator_control_bot import build_telegram_operator_control_summary
from pm_bot.trading_core.signer_boundary_models import FORCED_FALSE_EXECUTION_FIELDS
from pm_bot.trading_core.signer_boundary_preflight import (
    signer_boundary_preflight_artifact_paths,
    run_signer_boundary_preflight,
)
import pm_bot.trading_core.signer_boundary_preflight as signer_boundary_module
import pm_bot.trading_core.signer_boundary_models as signer_boundary_models

GENERATED_AT = "2026-05-14T00:00:00Z"

FAKE_SECRET_VALUES = (
    "fake-private-key-060",
    "fake-seed-phrase-060",
    "fake-mnemonic-060",
    "fake-api-secret-060",
)

FORBIDDEN_ARTIFACT_KEYS = {
    "order_id",
    "client_order_id",
    "tx_hash",
    "transaction_hash",
    "fill_id",
    "fill_price",
    "filled_size",
    "execution_price",
    "execution_status",
    "balance",
    "pnl",
    "profit",
    "realized_pnl",
    "unrealized_pnl",
    "position_opened",
    "position_closed",
    "signature",
    "signed_payload_value",
}


def _minimal_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {
        "PYTHONPATH": str(Path.cwd()),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "COMSPEC": os.environ.get("COMSPEC", ""),
        "PATH": os.environ.get("PATH", ""),
    }
    env.update(dict(extra or {}))
    return env


def _source_intent(path: Path, *, market: str = "BTC", strategy: str = "tiny-momentum") -> None:
    payload = {
        "contract_version": "pmbot_paper_trading_loop_intent_053.v1",
        "artifact_run_id": "paper-trading-loop-053-test",
        "paper_intent_ref": "paper-intent-ref-053-test",
        "strategy_name": strategy,
        "market_symbol": market,
        "market": market,
        "outcome": "Yes",
        "side": "paper_track_outcome",
        "limit_price": 0.52,
        "size": 1.0,
        "notional": 0.52,
        "confidence": 0.72,
        "signal_reason": "test paper intent",
        "risk_decision": "APPROVED_FOR_PAPER_INTENT",
        "paper_intent_status": "paper_intent_review_ready",
        "intent_is_not_order_submission": True,
        "is_execution_identifier": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
        "generated_at": GENERATED_AT,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _patch_source_paths(monkeypatch: Any, source_path: Path | None) -> None:
    missing = source_path.parent / "missing.json" if source_path else Path("missing-source-060.json")
    monkeypatch.setattr(
        signer_boundary_module,
        "DEFAULT_PAPER_INTENT_053_PATH",
        source_path or missing,
    )
    monkeypatch.setattr(
        signer_boundary_module,
        "DEFAULT_PAPER_RESULT_053_PATH",
        missing.with_name("missing_result_053.json"),
    )
    monkeypatch.setattr(
        signer_boundary_module,
        "DEFAULT_PUBLIC_MARKET_INTENT_054_PATH",
        missing.with_name("missing_public_intent_054.json"),
    )
    monkeypatch.setattr(
        signer_boundary_module,
        "DEFAULT_PUBLIC_MARKET_RESULT_054_PATH",
        missing.with_name("missing_public_result_054.json"),
    )


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if Path(path).exists():
            chunks.append(Path(path).read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    assert value["execution_mode"] == "preflight"
    assert value["review_only"] is True
    assert value["preflight_only"] is True
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        assert value[field] is False, field
    assert value["live_execution_approved"] is False
    assert value["canary_executable_now"] is False
    assert value["real_execution_available"] is False
    assert value["order_submission_enabled"] is False
    assert value["wallet_signing_enabled"] is False
    assert value["signing_enabled"] is False
    assert value["signed_payload_generation_enabled"] is False
    assert value["signed_order_generation_enabled"] is False
    assert value["authenticated_polymarket_enabled"] is False
    assert value["live_connector_enabled"] is False
    assert value["allowed_for_live"] is False
    assert value["resolved_blocker_count"] == 0


def _walk_keys(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        keys = [str(key) for key in value]
        for nested in value.values():
            keys.extend(_walk_keys(nested))
        return keys
    if isinstance(value, list):
        keys: list[str] = []
        for nested in value:
            keys.extend(_walk_keys(nested))
        return keys
    return []


def _blocker_ids(result: Mapping[str, Any]) -> set[str]:
    return {str(row.get("blocker_id")) for row in result.get("blockers", []) if isinstance(row, Mapping)}


def test_cli_runs_without_private_keys_and_writes_artifacts(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.signer_boundary_preflight",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(
            {
                "PRIVATE_KEY": FAKE_SECRET_VALUES[0],
                "POLYMARKET_PK": FAKE_SECRET_VALUES[1],
                "POLYGON_WALLET_PRIVATE_KEY": FAKE_SECRET_VALUES[2],
            }
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = signer_boundary_preflight_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    artifact_text = _artifact_text(paths)

    assert completed.returncode == 0, completed.stderr
    assert "Signer boundary preflight completed." in completed.stdout
    assert "Unsigned payload plan: schema_only_non_executable" in completed.stdout
    assert "Signer: blocked" in completed.stdout
    assert "Signed payload: unavailable" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert result["validation"]["valid"] is True
    for fake in FAKE_SECRET_VALUES:
        assert fake not in artifact_text


def test_missing_source_paper_intent_writes_blocker_and_does_not_crash(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _patch_source_paths(monkeypatch, None)
    exit_code = signer_boundary_runner.main(
        [
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path),
        ]
    )
    paths = signer_boundary_preflight_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert exit_code == 0
    assert result["status"] == "signer_boundary_preflight_incomplete_missing_source_live_blocked"
    assert result["live_candidate_order_intent"]["status"] == "missing_source"
    assert "missing_source_paper_intent" in _blocker_ids(result)
    assert paths["latest_status"].exists()
    _assert_required_false_flags(result)


def test_source_paper_intent_creates_non_executable_live_candidate_intent(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    source_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    _source_intent(source_path)
    _patch_source_paths(monkeypatch, source_path)
    result = run_signer_boundary_preflight(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    candidate = result["live_candidate_order_intent"]

    assert candidate["status"] == "created"
    assert candidate["candidate_intent_is_non_executable"] is True
    assert candidate["candidate_intent_is_not_order_submission"] is True
    assert candidate["candidate_outcome"] == "Yes"
    assert candidate["candidate_side"] == "paper_track_outcome"
    assert candidate["candidate_limit_price"] == 0.52
    assert candidate["candidate_size"] == 1.0
    assert candidate["candidate_notional"] == 0.52
    _assert_required_false_flags(candidate)
    _assert_required_false_flags(result)


def test_unsigned_plan_is_schema_only_and_non_executable(tmp_path: Path, monkeypatch: Any) -> None:
    source_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    _source_intent(source_path)
    _patch_source_paths(monkeypatch, source_path)
    result = run_signer_boundary_preflight(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    plan = result["unsigned_order_payload_plan"]

    assert plan["status"] == "schema_only_non_executable"
    assert plan["unsigned_plan_created"] is True
    assert plan["unsigned_plan_is_executable"] is False
    assert plan["schema_only"] is True
    assert plan["payload_materialized"] is False
    assert plan["real_clob_payload_materialized"] is False
    assert plan["ready_for_signing"] is False
    _assert_required_false_flags(plan)


def test_signer_signed_payload_submission_wallet_balance_position_boundaries_stay_blocked(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    source_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    _source_intent(source_path)
    _patch_source_paths(monkeypatch, source_path)
    result = run_signer_boundary_preflight(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )

    assert result["signing_boundary_status"]["signer_blocked"] is True
    assert result["signing_boundary_status"]["signer_config_present"] is False
    assert result["signing_boundary_status"]["signer_instantiated"] is False
    assert result["signed_payload_availability"]["signed_payload_available"] is False
    assert result["signed_payload_availability"]["signed_payload_generated"] is False
    assert result["order_submission_availability"]["order_submission_available"] is False
    assert result["order_submission_availability"]["order_submission_attempted"] is False
    assert result["order_submission_availability"]["order_cancellation_attempted"] is False
    assert result["balance_read_attempted"] is False
    assert result["position_read_attempted"] is False
    _assert_required_false_flags(result)


def test_no_private_key_env_vars_wallet_signer_libraries_or_signing_calls_are_used() -> None:
    source = (
        inspect.getsource(signer_boundary_module)
        + "\n"
        + inspect.getsource(signer_boundary_models)
    ).lower()
    forbidden_terms = (
        "os.environ",
        "getenv",
        "environ[",
        "polymarket_pk",
        "polygon_wallet_private_key",
        "py_clob_client",
        "clobclient",
        "eth_account",
        "web3",
        "account.from_key",
        ".sign(",
        "sign_typed_data",
        "eip712",
        "create_order",
        "post_order",
        "submit_order",
        "cancel_order",
        "get_balance",
        "get_balances",
        "get_position",
        "get_positions",
        "requests.",
        "httpx.",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_artifacts_exclude_fake_secrets_signatures_payloads_ids_fills_balances_positions_and_pnl(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    source_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    _source_intent(source_path)
    _patch_source_paths(monkeypatch, source_path)
    result = run_signer_boundary_preflight(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = signer_boundary_preflight_artifact_paths(tmp_path / "artifacts")
    artifact_text = _artifact_text(paths)
    forbidden_fake_values = (
        "fake-private-key-060",
        "fake-signature-060",
        "fake-signed-payload-060",
        "fake-order-id-060",
        "fake-client-order-id-060",
        "fake-tx-hash-060",
        "fake-fill-060",
        "fake-balance-060",
        "fake-pnl-060",
        "fake-position-060",
    )

    for fake in forbidden_fake_values:
        assert fake not in artifact_text
    keys = set(_walk_keys(result))
    assert not (keys & FORBIDDEN_ARTIFACT_KEYS)


def test_latest_status_and_operator_markdown_are_written(tmp_path: Path, monkeypatch: Any) -> None:
    source_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    _source_intent(source_path)
    _patch_source_paths(monkeypatch, source_path)
    result = run_signer_boundary_preflight(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = signer_boundary_preflight_artifact_paths(tmp_path / "artifacts")
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    markdown = paths["operator_md"].read_text(encoding="utf-8")

    assert latest_status["status"] == result["status"]
    assert latest_status["live_candidate_intent_status"] == "created"
    assert "Signer blocked" in markdown
    assert "Signed payload unavailable" in markdown
    assert "Order submission blocked" in markdown
    assert "Live execution blocked" in markdown
    assert "review signer boundary only, no live order available" in markdown
    _assert_required_false_flags(latest_status)


def test_ui_and_telegram_passive_summaries_include_060_status(tmp_path: Path, monkeypatch: Any) -> None:
    source_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    _source_intent(source_path)
    _patch_source_paths(monkeypatch, source_path)
    result = run_signer_boundary_preflight(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    latest_status = result["latest_status"]
    panel = build_operator_ui_panel_v1(
        dashboard={"signer_boundary_preflight_status_summary": latest_status},
        latest_paths={"signer_boundary_preflight_status": latest_status["latest_status_path"]},
        generated_at=GENERATED_AT,
    )
    panel_summary = summarize_operator_ui_panel_v1(panel)
    telegram_summary = build_telegram_operator_control_summary(
        context={"signer_boundary_preflight_status_summary": latest_status},
        generated_at=GENERATED_AT,
    )

    assert panel["signer_boundary_preflight_section_ready"] is True
    assert panel_summary["signer_boundary_preflight_status"] == "signer_boundary_preflight_completed_live_blocked"
    assert panel_summary["signer_boundary_live_candidate_intent_status"] == "created"
    assert panel_summary["signer_boundary_unsigned_plan_status"] == "schema_only_non_executable"
    assert panel_summary["signer_boundary_unsigned_plan_is_executable"] is False
    assert panel_summary["signer_boundary_signer_blocked"] is True
    assert panel_summary["signer_boundary_signed_payload_unavailable"] is True
    assert panel_summary["signer_boundary_order_submission_blocked"] is True
    assert panel_summary["signer_boundary_live_execution_blocked"] is True
    signer_summary = telegram_summary["signer_boundary_preflight_status_summary"]
    assert signer_summary["live_candidate_intent_status"] == "created"
    assert signer_summary["unsigned_plan_status"] == "schema_only_non_executable"
    assert signer_summary["signer_blocked"] is True
    assert signer_summary["signed_payload_unavailable"] is True
    assert signer_summary["order_submission_blocked"] is True
    assert signer_summary["live_execution_blocked"] is True
    assert telegram_summary["no_executable_live_action"] is True


def test_existing_052_053_054_055_056_057_058_059_commands_still_work(tmp_path: Path) -> None:
    env = _minimal_env({"PMBOT_GAMMA_BASE_URL": "http://127.0.0.1:1"})
    commands = [
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_canary_drill",
            "--market",
            "BTC",
            "--dry-run",
            "--artifact-dir",
            str(tmp_path / "paper_canary_drill_052"),
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
            str(tmp_path / "paper_trading_loop_053"),
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
            str(tmp_path / "public_market_paper_loop_054"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_decision_ledger",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--source",
            "public_market_loop_054",
            "--artifacts-dir",
            str(tmp_path / "paper_decision_ledger_055"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.live_connector_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "live_connector_preflight_056"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.authenticated_clob_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--mock-auth",
            "--artifacts-dir",
            str(tmp_path / "authenticated_clob_preflight_057"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.authenticated_clob_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--no-order-auth-get",
            "--artifacts-dir",
            str(tmp_path / "no_order_auth_get_059"),
        ],
    ]
    outputs = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=Path.cwd(),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        outputs.append(completed.stdout)
        assert completed.returncode == 0, completed.stderr

    assert "Paper canary drill completed." in outputs[0]
    assert "Paper trading loop completed." in outputs[1]
    assert "Public market paper loop completed." in outputs[2]
    assert "Paper decision ledger updated." in outputs[3]
    assert "Live connector preflight completed." in outputs[4]
    assert "Authenticated CLOB preflight completed." in outputs[5]
    assert "No-order auth GET: mocked" in outputs[6]
    assert all("Live execution: blocked" in output for output in outputs)


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    runtime_files = (
        Path("pm_bot/trading_core/signer_boundary_models.py"),
        Path("pm_bot/trading_core/signer_boundary_preflight.py"),
        Path("pm_bot/operator_runner/signer_boundary_preflight.py"),
        Path("pm_bot/operator_runner/operator_ui_panel_v1.py"),
        Path("pm_bot/operator_runner/telegram_operator_control_bot.py"),
    )
    forbidden_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.")
    for path in runtime_files:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_terms:
            assert term not in lowered, path
