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
from pm_bot.operator_runner.telegram_operator_control_bot import build_telegram_operator_control_summary
from pm_bot.trading_core.static_safety_invariant_report import run_static_safety_invariant_report
from pm_bot.trading_core.tiny_order_scaffold import (
    tiny_order_scaffold_artifact_paths,
    run_tiny_order_scaffold,
)
import pm_bot.operator_runner.tiny_order_scaffold as tiny_runner
import pm_bot.trading_core.tiny_order_scaffold as tiny_module
import pm_bot.trading_core.tiny_order_scaffold_models as tiny_models
from pm_bot.trading_core.tiny_order_scaffold_models import FORCED_FALSE_EXECUTION_FIELDS

GENERATED_AT = "2026-05-15T00:00:00+04:00"

FAKE_SECRET_VALUES = (
    "fake-private-key-061",
    "fake-seed-phrase-061",
    "fake-mnemonic-061",
    "fake-api-secret-061",
)

FORBIDDEN_ARTIFACT_KEYS = {
    "order_id",
    "client_order_id",
    "tx_hash",
    "transaction_hash",
    "fill_id",
    "fill_price",
    "filled_size",
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


def _source_intent(
    path: Path,
    *,
    market: str = "BTC",
    strategy: str = "tiny-momentum",
    limit_price: float = 0.52,
    size: float = 1.0,
    notional: float = 0.52,
) -> None:
    payload = {
        "contract_version": "pmbot_paper_trading_loop_intent_053.v1",
        "strategy_name": strategy,
        "market_symbol": market,
        "market": market,
        "outcome": "Yes",
        "side": "paper_track_outcome",
        "limit_price": limit_price,
        "size": size,
        "notional": notional,
        "paper_intent_status": "paper_intent_review_ready",
        "intent_is_not_order_submission": True,
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


def _signer_status(
    path: Path,
    *,
    source_intent_path: str,
    market: str = "BTC",
    strategy: str = "tiny-momentum",
    limit_price: float = 0.52,
    size: float = 1.0,
    notional: float = 0.52,
) -> None:
    payload = {
        "contract_version": "pmbot_latest_signer_boundary_preflight_status_060.v1",
        "status": "signer_boundary_preflight_completed_live_blocked",
        "market_symbol": market,
        "market": market,
        "strategy_name": strategy,
        "source_paper_intent_path": source_intent_path,
        "candidate_outcome": "Yes",
        "candidate_side": "paper_track_outcome",
        "candidate_limit_price": limit_price,
        "candidate_size": size,
        "candidate_notional": notional,
        "live_candidate_intent_status": "created",
        "unsigned_plan_status": "schema_only_non_executable",
        "signer_status": "blocked",
        "signed_payload_status": "unavailable",
        "order_submission_status": "blocked",
        "signer_config_present": False,
        "signed_payload_available": False,
        "order_submission_available": False,
        "signer_instantiated": False,
        "signing_attempted": False,
        "signed_payload_generated": False,
        "order_submission_attempted": False,
        "order_cancellation_attempted": False,
        "wallet_connection_attempted": False,
        "balance_read_attempted": False,
        "position_read_attempted": False,
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


def _patch_source_paths(monkeypatch: Any, *, signer_path: Path | None = None, paper_path: Path | None = None) -> None:
    missing_root = (signer_path or paper_path or Path("missing-source-061.json")).parent
    missing = missing_root / "missing-source-061.json"
    monkeypatch.setattr(tiny_module, "DEFAULT_SIGNER_BOUNDARY_LATEST_STATUS_060_PATH", signer_path or missing)
    monkeypatch.setattr(tiny_module, "DEFAULT_SIGNER_BOUNDARY_RESULT_060_PATH", missing.with_name("missing-result-060.json"))
    monkeypatch.setattr(
        tiny_module,
        "DEFAULT_SIGNER_BOUNDARY_CANDIDATE_060_PATH",
        missing.with_name("missing-candidate-060.json"),
    )
    monkeypatch.setattr(tiny_module, "DEFAULT_PAPER_INTENT_053_PATH", paper_path or missing)
    monkeypatch.setattr(tiny_module, "DEFAULT_PAPER_RESULT_053_PATH", missing.with_name("missing-result-053.json"))
    monkeypatch.setattr(
        tiny_module,
        "DEFAULT_PUBLIC_MARKET_INTENT_054_PATH",
        missing.with_name("missing-public-intent-054.json"),
    )
    monkeypatch.setattr(
        tiny_module,
        "DEFAULT_PUBLIC_MARKET_RESULT_054_PATH",
        missing.with_name("missing-public-result-054.json"),
    )


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if Path(path).exists():
            chunks.append(Path(path).read_text(encoding="utf-8"))
    return "\n".join(chunks)


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


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    assert value["execution_mode"] == "preflight"
    assert value["review_only"] is True
    assert value["preflight_only"] is True
    assert value["scaffold_only"] is True
    assert value["approval_required"] is True
    assert value["operator_approved"] is False
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


def _blocker_ids(result: Mapping[str, Any]) -> set[str]:
    return {str(row.get("blocker_id")) for row in result.get("blockers", []) if isinstance(row, Mapping)}


def test_cli_runs_without_private_keys_and_writes_review_only_artifacts(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.tiny_order_scaffold",
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
    paths = tiny_order_scaffold_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    artifact_text = _artifact_text(paths)

    assert completed.returncode == 0, completed.stderr
    assert "Tiny order scaffold completed." in completed.stdout
    assert "Tiny candidate: created" in completed.stdout
    assert "Approval packet: created" in completed.stdout
    assert "Operator approved: false" in completed.stdout
    assert "Signing: blocked" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Live execution: blocked" in completed.stdout
    assert result["validation"]["valid"] is True
    for fake in FAKE_SECRET_VALUES:
        assert fake not in artifact_text


def test_missing_source_writes_blocker_incomplete_status_and_does_not_crash(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _patch_source_paths(monkeypatch)
    exit_code = tiny_runner.main(
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
    paths = tiny_order_scaffold_artifact_paths(tmp_path)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert exit_code == 0
    assert result["status"] == "tiny_order_scaffold_incomplete_missing_source_live_blocked"
    assert result["tiny_order_candidate"]["status"] == "missing_source"
    assert result["hard_limits_passed"] is False
    assert result["approval_packet_created"] is False
    assert {"missing_source", "hard_limits_not_passed", "approval_packet_not_created"}.issubset(
        _blocker_ids(result)
    )
    assert paths["latest_status"].exists()
    _assert_required_false_flags(result)


def test_latest_signer_boundary_source_creates_non_executable_tiny_candidate(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    paper_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    signer_path = tmp_path / "signer" / "latest_signer_boundary_preflight_status_060.json"
    _source_intent(paper_path)
    _signer_status(signer_path, source_intent_path=paper_path.as_posix())
    _patch_source_paths(monkeypatch, signer_path=signer_path)

    result = run_tiny_order_scaffold(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        from_latest_signer_boundary=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    candidate = result["tiny_order_candidate"]

    assert candidate["status"] == "created"
    assert candidate["source_signer_boundary_path"] == signer_path.as_posix()
    assert candidate["source_intent_path"] == paper_path.as_posix()
    assert candidate["candidate_outcome"] == "Yes"
    assert candidate["candidate_side"] == "paper_track_outcome"
    assert candidate["candidate_limit_price"] == 0.52
    assert candidate["candidate_size"] == 1.0
    assert candidate["candidate_notional"] == 0.52
    assert candidate["candidate_is_executable"] is False
    assert result["hard_limits_passed"] is True
    _assert_required_false_flags(candidate)
    _assert_required_false_flags(result)


def test_hard_limits_pass_for_tiny_candidate_and_manual_approval_packet_is_not_operator_approved(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    paper_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    _source_intent(paper_path)
    _patch_source_paths(monkeypatch, paper_path=paper_path)

    result = run_tiny_order_scaffold(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        from_latest_paper_intent=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    approval = result["manual_tiny_order_approval_packet"]

    assert result["hard_limits_passed"] is True
    assert result["tiny_order_hard_limits"]["hard_limits_passed"] is True
    assert result["approval_packet_created"] is True
    assert approval["approval_packet_created"] is True
    assert approval["approval_required"] is True
    assert approval["operator_approved"] is False
    assert approval["candidate_is_executable"] is False
    assert approval["operator_must_not_execute_from_packet"] is True
    _assert_required_false_flags(approval)


def test_hard_limits_block_oversized_candidate_in_temp_fixture(tmp_path: Path, monkeypatch: Any) -> None:
    paper_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    _source_intent(paper_path, limit_price=0.52, size=2.0, notional=1.04)
    _patch_source_paths(monkeypatch, paper_path=paper_path)

    result = run_tiny_order_scaffold(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        from_latest_paper_intent=True,
        max_notional=1.0,
        max_size=1.0,
        max_price=0.99,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == "tiny_order_scaffold_blocked_by_hard_limits_live_blocked"
    assert result["hard_limits_passed"] is False
    assert result["approval_packet_created"] is True
    assert "hard_limits_not_passed" in _blocker_ids(result)
    assert result["tiny_order_hard_limits"]["checks"][1]["passed"] is False
    assert result["tiny_order_hard_limits"]["checks"][2]["passed"] is False
    _assert_required_false_flags(result)


def test_signing_submission_wallet_account_and_live_execution_boundaries_stay_blocked(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    paper_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    _source_intent(paper_path)
    _patch_source_paths(monkeypatch, paper_path=paper_path)

    result = run_tiny_order_scaffold(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        from_latest_paper_intent=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    submission = result["tiny_order_submission_availability"]

    assert result["candidate_is_executable"] is False
    assert result["signing_attempted"] is False
    assert result["signed_payload_generated"] is False
    assert result["signed_payload_available"] is False
    assert result["order_submission_attempted"] is False
    assert result["order_submission_available"] is False
    assert result["order_cancellation_attempted"] is False
    assert result["wallet_connection_attempted"] is False
    assert result["balance_read_attempted"] is False
    assert result["position_read_attempted"] is False
    assert result["fill_read_attempted"] is False
    assert submission["signed_payload_unavailable"] is True
    assert submission["order_submission_blocked"] is True
    assert submission["order_cancellation_blocked"] is True
    assert submission["wallet_connection_blocked"] is True
    assert submission["live_execution_blocked"] is True
    _assert_required_false_flags(submission)


def test_no_private_key_wallet_signer_network_or_order_runtime_calls_are_used() -> None:
    source = (
        inspect.getsource(tiny_module)
        + "\n"
        + inspect.getsource(tiny_models)
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
        "get_fill",
        "get_fills",
        "get_pnl",
        "requests.",
        "httpx.",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_artifacts_exclude_fake_secrets_signed_payloads_ids_fills_balances_positions_and_pnl(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    paper_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    _source_intent(paper_path)
    _patch_source_paths(monkeypatch, paper_path=paper_path)

    result = run_tiny_order_scaffold(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        from_latest_paper_intent=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = tiny_order_scaffold_artifact_paths(tmp_path / "artifacts")
    artifact_text = _artifact_text(paths)
    forbidden_fake_values = (
        "fake-private-key-061",
        "fake-signature-061",
        "fake-signed-payload-061",
        "fake-order-id-061",
        "fake-client-order-id-061",
        "fake-tx-hash-061",
        "fake-fill-061",
        "fake-balance-061",
        "fake-pnl-061",
        "fake-position-061",
    )

    for fake in forbidden_fake_values:
        assert fake not in artifact_text
    keys = set(_walk_keys(result))
    assert not (keys & FORBIDDEN_ARTIFACT_KEYS)


def test_latest_status_and_operator_markdown_are_written(tmp_path: Path, monkeypatch: Any) -> None:
    paper_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    _source_intent(paper_path)
    _patch_source_paths(monkeypatch, paper_path=paper_path)
    result = run_tiny_order_scaffold(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        from_latest_paper_intent=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    paths = tiny_order_scaffold_artifact_paths(tmp_path / "artifacts")
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    markdown = paths["operator_md"].read_text(encoding="utf-8")

    assert latest_status["status"] == result["status"]
    assert latest_status["tiny_candidate"] == "created"
    assert latest_status["manual_tiny_order_approval_packet_path"].endswith(
        "manual_tiny_order_approval_packet_061.json"
    )
    assert "approval required" in markdown
    assert "operator approved=false" in markdown
    assert "candidate executable=false" in markdown
    assert "signing blocked" in markdown
    assert "order submission blocked" in markdown
    assert "wallet blocked" in markdown
    assert "live execution blocked" in markdown
    assert "review packet only; no live order available" in markdown
    _assert_required_false_flags(latest_status)


def test_ui_and_telegram_passive_summaries_include_061_status(tmp_path: Path, monkeypatch: Any) -> None:
    paper_path = tmp_path / "source" / "paper_trading_order_intent_053.json"
    _source_intent(paper_path)
    _patch_source_paths(monkeypatch, paper_path=paper_path)
    result = run_tiny_order_scaffold(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        from_latest_paper_intent=True,
        artifact_dir=tmp_path / "artifacts",
        generated_at=GENERATED_AT,
    )
    latest_status = result["latest_status"]
    panel = build_operator_ui_panel_v1(
        dashboard={"tiny_order_scaffold_status_summary": latest_status},
        latest_paths={"tiny_order_scaffold_status": latest_status["latest_status_path"]},
        generated_at=GENERATED_AT,
    )
    panel_summary = summarize_operator_ui_panel_v1(panel)
    telegram_summary = build_telegram_operator_control_summary(
        context={"tiny_order_scaffold_status_summary": latest_status},
        generated_at=GENERATED_AT,
    )

    assert panel["tiny_order_scaffold_section_ready"] is True
    assert panel_summary["tiny_order_scaffold_status"] == "tiny_order_scaffold_completed_live_blocked"
    assert panel_summary["tiny_order_scaffold_tiny_candidate"] == "created"
    assert panel_summary["tiny_order_scaffold_approval_packet"] == "created"
    assert panel_summary["tiny_order_scaffold_operator_approved"] is False
    assert panel_summary["tiny_order_scaffold_order_submission_blocked"] is True
    assert panel_summary["tiny_order_scaffold_signer_blocked"] is True
    assert panel_summary["tiny_order_scaffold_live_execution_blocked"] is True
    tiny_summary = telegram_summary["tiny_order_scaffold_status_summary"]
    assert tiny_summary["tiny_candidate"] == "created"
    assert tiny_summary["operator_approved"] is False
    assert tiny_summary["order_submission_blocked"] is True
    assert tiny_summary["signed_payload_unavailable"] is True
    assert tiny_summary["live_execution_blocked"] is True
    assert telegram_summary["no_executable_live_action"] is True


def test_static_safety_scanner_passes_with_critical_zero(tmp_path: Path) -> None:
    report = run_static_safety_invariant_report(
        scope="pm_bot",
        dry_run=True,
        artifact_dir=tmp_path / "scanner",
        generated_at=GENERATED_AT,
    )

    assert report["critical_count"] == 0
    assert report["safety_ok"] is True


def test_existing_052_to_060_focused_commands_still_have_blocked_live_summaries(tmp_path: Path) -> None:
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
            str(tmp_path / "signer_boundary_preflight_060"),
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
    assert "Signer boundary preflight completed." in outputs[7]
    assert all("Live execution: blocked" in output for output in outputs)


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    runtime_files = (
        Path("pm_bot/trading_core/tiny_order_scaffold_models.py"),
        Path("pm_bot/trading_core/tiny_order_scaffold.py"),
        Path("pm_bot/operator_runner/tiny_order_scaffold.py"),
    )
    forbidden_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.", "daemon=true")
    for path in runtime_files:
        lowered = path.read_text(encoding="utf-8").lower().replace(" ", "")
        for term in forbidden_terms:
            assert term.replace(" ", "") not in lowered, path
