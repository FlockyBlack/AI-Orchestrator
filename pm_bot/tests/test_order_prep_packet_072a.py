from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.order_prep_packet import order_prep_packet_artifact_paths, run_order_prep_packet
import pm_bot.trading_core.order_prep_packet as packet_module
import pm_bot.trading_core.order_prep_packet_models as models_module
from pm_bot.trading_core.order_prep_packet_models import (
    REQUIRED_FALSE_FLAGS,
    SOURCE_ACCOUNT_PROBE_070C,
    SOURCE_APPROVAL_CONTRACT_065D,
    SOURCE_SIGNED_PAYLOAD_DRY_RUN_070A,
    SOURCE_SIGNER_DIAGNOSTIC_069A,
    STATUS_BLOCKED,
    validate_order_prep_packet_result,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"
TOKEN_ID = "12345678901234567890072"
SECOND_TOKEN_ID = "12345678901234567890073"
RAW_PRIVATE_KEY = "0x" + "7" * 64
RAW_SECRET_VALUES = (
    "private-key-marker-072a",
    "api-secret-marker-072a",
    "passphrase-marker-072a",
    '{"maker":"0xabc","signature":"full-signed-payload-marker-072a"}',
)
FAKE_EXECUTION_VALUES = (
    "fake-order-id-072a",
    "fake-tx-hash-072a",
    "fake-fill-072a",
    "fake-pnl-072a",
)

REQUIRED_ARTIFACT_NAMES = {
    "order_prep_packet_072a_result.json",
    "latest_order_prep_packet_status_072a.json",
    "order_prep_packet_sources_072a.json",
    "order_prep_packet_operator_review_072a.json",
    "order_prep_packet_blockers_072a.json",
    "order_prep_packet_safety_snapshot_072a.json",
    "order_prep_packet_operator_summary_072a.md",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/order_prep_packet_models.py"),
    Path("pm_bot/trading_core/order_prep_packet.py"),
    Path("pm_bot/operator_runner/order_prep_packet.py"),
)


def _minimal_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {
        "PYTHONPATH": str(Path.cwd()),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "COMSPEC": os.environ.get("COMSPEC", ""),
        "PATH": os.environ.get("PATH", ""),
    }
    env.update(dict(extra or {}))
    return env


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_ready_source_artifacts(root: Path, *, multiple_tokens: bool = False, selected_token: bool = True) -> None:
    token_values = [TOKEN_ID, SECOND_TOKEN_ID] if multiple_tokens else [TOKEN_ID]
    _write_json(
        root / "public_market_token_discovery_071a" / "public_market_token_discovery_071a_result.json",
        {
            "contract_version": "pmbot_public_market_token_discovery_result_071a.v1",
            "status": "source_backed_candidates_ready",
            "market": "BTC",
            "strategy": "tiny-momentum",
            "market_candidate_count": 1,
            "outcome_token_candidate_count": len(token_values),
            "outcome_token_candidates": [
                {
                    "token_candidate_id": f"token-candidate-072a-{index}",
                    "market_candidate_id": "market-candidate-072a",
                    "market_slug": "bitcoin-up-or-down-072a",
                    "outcome_name": "Yes" if index == 0 else "No",
                    "token_id": token_id,
                    "source_backed": True,
                    "token_id_is_source_backed": True,
                    "token_id_is_generated": False,
                }
                for index, token_id in enumerate(token_values)
            ],
        },
    )
    bridge_target = {"token_id": TOKEN_ID, "market_slug": "bitcoin-up-or-down-072a"} if selected_token else {}
    _write_json(
        root / "discovery_to_token_resolver_bridge_071d" / "discovery_to_token_resolver_bridge_071d_result.json",
        {
            "contract_version": "pmbot_discovery_to_token_resolver_bridge_071d_result.v1",
            "status": "target_candidate_contract_ready_review_only" if selected_token else "operator_selection_required_multiple_source_backed_candidates",
            "target_contract": bridge_target,
            "operator_selection_required": {"selection_required": multiple_tokens and not selected_token},
            "valid_source_backed_candidates": [
                {
                    "bridge_candidate_id": f"bridge-candidate-072a-{index}",
                    "source_token_candidate_id": f"token-candidate-072a-{index}",
                    "market_slug": "bitcoin-up-or-down-072a",
                    "outcome_name": "Yes" if index == 0 else "No",
                    "token_id": token_id,
                    "source_backed": True,
                }
                for index, token_id in enumerate(token_values)
            ],
        },
    )
    _write_json(
        root / "first_order_market_token_resolver_070b" / "first_order_market_token_resolver_070b_result.json",
        {
            "contract_version": "pmbot_first_order_market_token_resolver_070b_result.v1",
            "status": "target_contract_ready_review_only" if selected_token else "blocked_missing_token_id",
            "target_contract": {"token_id": TOKEN_ID if selected_token else ""},
        },
    )
    _write_json(
        root / "live_account_readonly_state_probe_070c" / "live_account_readonly_state_probe_070c_result.json",
        {
            "contract_version": "pmbot_live_account_readonly_state_probe_result_070c.v1",
            "status": "account_readonly_probe_ok",
            "account_state_probe_performed": True,
            "account_readonly_ok": True,
            "raw_private_key": RAW_PRIVATE_KEY,
            "api_secret_value": RAW_SECRET_VALUES[1],
            "fake_execution_marker": FAKE_EXECUTION_VALUES[0],
        },
    )
    _write_json(
        root / "live_readonly_status_aggregator_071b" / "live_readonly_status_aggregator_071b_result.json",
        {
            "contract_version": "pmbot_live_readonly_status_aggregator_071b_result.v1",
            "status": "live_readonly_status_aggregated",
            "latest_status": {"status": "live_readonly_status_aggregated"},
        },
    )
    _write_json(
        root / "guarded_signer_diagnostic_smoke_069a" / "guarded_signer_diagnostic_smoke_069a_result.json",
        {
            "contract_version": "pmbot_guarded_signer_diagnostic_smoke_069a.v1",
            "status": "diagnostic_ok",
            "diagnostic_status": "diagnostic_ok",
            "private_key_value": RAW_SECRET_VALUES[0],
        },
    )
    _write_json(
        root / "first_live_order_approval_contract_065d" / "first_live_order_approval_contract_065d_result.json",
        {
            "contract_version": "pmbot_first_live_order_approval_contract_065d.v1",
            "status": "operator_approval_recorded_review_only",
            "operator_approval_recorded": True,
            "approval_contract_executable": False,
            "allowed_for_live": False,
        },
    )
    _write_json(
        root / "signed_order_payload_dry_run_070a" / "signed_order_payload_dry_run_070a_result.json",
        {
            "contract_version": "pmbot_signed_order_payload_dry_run_070a_result.v1",
            "status": "blocked_non_executable_signed_order_payload_dry_run_no_submit",
            "order_payload_contract_built": True,
            "payload_contract": {"contract_only": True, "token_id_present": True},
            "full_signed_payload": RAW_SECRET_VALUES[3],
        },
    )


def _walk_mappings(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        rows: list[Mapping[str, Any]] = [value]
        for nested in value.values():
            rows.extend(_walk_mappings(nested))
        return rows
    if isinstance(value, list):
        rows = []
        for nested in value:
            rows.extend(_walk_mappings(nested))
        return rows
    return []


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    for row in _walk_mappings(value):
        for field in REQUIRED_FALSE_FLAGS:
            if field in row:
                assert row[field] is False, field
        if "resolved_blocker_count" in row:
            assert row["resolved_blocker_count"] == 0


def _assert_blocker(result: Mapping[str, Any], blocker_id: str) -> None:
    assert result["packet_blocked"] is True
    assert result["status"] == STATUS_BLOCKED
    assert blocker_id in {row["blocker_id"] for row in result["blockers"]}


def test_missing_artifacts_produce_blocked_unknown_without_fake_data(tmp_path: Path) -> None:
    result = run_order_prep_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "missing",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["packet_blocked"] is True
    assert result["selected_token_id"] == ""
    assert result["selected_token_id_present"] is False
    assert result["sources"]["available_source_count"] == 0
    assert result["sources"]["missing_source_count"] == 8
    assert all(row["status"] in {"missing", "unreadable"} for row in result["sources"]["sources"].values())
    assert validate_order_prep_packet_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_multiple_source_backed_token_candidates_require_operator_selection(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources", multiple_tokens=True, selected_token=False)

    result = run_order_prep_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["operator_selection_required"] is True
    assert result["selected_token_id"] == ""
    assert result["source_backed_token_candidate_count"] == 2
    _assert_blocker(result, "operator_selection_required")
    _assert_blocker(result, "missing_selected_token_id")


def test_no_selected_token_id_blocks_packet(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources", selected_token=False)

    result = run_order_prep_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["operator_selection_required"] is False
    assert result["selected_token_id_present"] is False
    _assert_blocker(result, "missing_selected_token_id")


def test_signer_diagnostic_missing_blocks_packet(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources")
    missing = tmp_path / "sources" / SOURCE_SIGNER_DIAGNOSTIC_069A / "guarded_signer_diagnostic_smoke_069a_result.json"
    missing.unlink()

    result = run_order_prep_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    _assert_blocker(result, f"missing_{SOURCE_SIGNER_DIAGNOSTIC_069A}")
    _assert_blocker(result, "signer_diagnostic_missing_or_not_ok")


def test_account_status_missing_or_failed_blocks_packet(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "missing")
    (tmp_path / "missing" / SOURCE_ACCOUNT_PROBE_070C / "live_account_readonly_state_probe_070c_result.json").unlink()
    missing_result = run_order_prep_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "missing",
        artifact_dir=tmp_path / "out_missing",
        generated_at=GENERATED_AT,
    )

    _write_ready_source_artifacts(tmp_path / "failed")
    _write_json(
        tmp_path / "failed" / SOURCE_ACCOUNT_PROBE_070C / "live_account_readonly_state_probe_070c_result.json",
        {
            "contract_version": "pmbot_live_account_readonly_state_probe_result_070c.v1",
            "status": "failed_account_probe",
            "account_state_probe_performed": False,
        },
    )
    failed_result = run_order_prep_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "failed",
        artifact_dir=tmp_path / "out_failed",
        generated_at=GENERATED_AT,
    )

    _assert_blocker(missing_result, f"missing_{SOURCE_ACCOUNT_PROBE_070C}")
    _assert_blocker(missing_result, "account_probe_missing_or_failed")
    _assert_blocker(failed_result, "account_probe_missing_or_failed")


def test_approval_missing_blocks_packet(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources")
    (tmp_path / "sources" / SOURCE_APPROVAL_CONTRACT_065D / "first_live_order_approval_contract_065d_result.json").unlink()

    result = run_order_prep_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    _assert_blocker(result, f"missing_{SOURCE_APPROVAL_CONTRACT_065D}")
    _assert_blocker(result, "operator_approval_missing")


def test_signed_payload_dry_run_missing_blocks_packet(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources")
    (tmp_path / "sources" / SOURCE_SIGNED_PAYLOAD_DRY_RUN_070A / "signed_order_payload_dry_run_070a_result.json").unlink()

    result = run_order_prep_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    _assert_blocker(result, f"missing_{SOURCE_SIGNED_PAYLOAD_DRY_RUN_070A}")
    _assert_blocker(result, "signed_payload_dry_run_missing")


def test_required_hard_safety_flags_are_false(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources")

    result = run_order_prep_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["allowed_for_live"] is False
    assert result["order_prep_packet_executable"] is False
    assert result["order_submission_enabled"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_no_submit_cancel_write_endpoint_or_signing_runtime_calls_exist() -> None:
    source = (
        inspect.getsource(packet_module)
        + "\n"
        + inspect.getsource(models_module)
        + "\n"
        + Path("pm_bot/operator_runner/order_prep_packet.py").read_text(encoding="utf-8")
    ).lower()
    forbidden_terms = (
        "requests.",
        "httpx.",
        "urllib.request",
        ".post(",
        ".put(",
        ".patch(",
        ".delete(",
        "create_order(",
        "post_order(",
        "submit_order(",
        "place_order(",
        "send_order(",
        "execute_order(",
        "cancel_order(",
        "delete_order(",
        "submit_cancel(",
        "cancel_all_orders(",
        "sign_order(",
        "sign_payload(",
        "create_signed_order(",
        "generate_signed_payload(",
        "account.from_key",
        "sign_typed_data",
        "eip712",
        "web3",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_no_private_key_api_secret_passphrase_or_full_signed_payload_output(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path / "sources")

    run_order_prep_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    paths = order_prep_packet_artifact_paths(tmp_path / "out")
    artifact_text = "\n".join(path.read_text(encoding="utf-8") for key, path in paths.items() if key != "root")

    for secret in (RAW_PRIVATE_KEY, *RAW_SECRET_VALUES):
        assert secret not in artifact_text
    for fake in FAKE_EXECUTION_VALUES:
        assert fake not in artifact_text


def test_runner_emits_required_artifacts_only(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.order_prep_packet",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifact-root",
            str(tmp_path / "missing_sources"),
            "--artifacts-dir",
            str(tmp_path / "out"),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = order_prep_packet_artifact_paths(tmp_path / "out")
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Order prep packet 072A completed." in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Order prep packet executable: false" in completed.stdout
    assert "Order submission enabled: false" in completed.stdout
    assert set(p.name for p in (tmp_path / "out").iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert result["packet_blocked"] is True
    assert result["validation"]["valid"] is True


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.", "start-process")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert re.search(re.escape(term), lowered) is None, path
