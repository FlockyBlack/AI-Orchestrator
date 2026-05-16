from __future__ import annotations

import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.operator_runner.selected_token_verification_bridge as runner_module
import pm_bot.trading_core.selected_token_verification_bridge as bridge_module
import pm_bot.trading_core.selected_token_verification_models as models_module
from pm_bot.trading_core.selected_token_payload_readiness_gate import run_selected_token_payload_readiness_gate
from pm_bot.trading_core.selected_token_payload_readiness_models import (
    STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC_EVIDENCE,
    STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN,
)
from pm_bot.trading_core.selected_token_verification_bridge import (
    run_selected_token_verification_bridge,
    selected_token_verification_artifact_paths,
)
from pm_bot.trading_core.selected_token_verification_models import (
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE_ARTIFACT,
    STATUS_BLOCKED_SELECTED_TOKEN_NOT_SOURCE_VERIFIED,
    STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN,
    validate_selected_token_verification_result,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"
RAW_TOKEN_ID_1 = "123456789012345678900761"
RAW_TOKEN_ID_2 = "123456789012345678900762"

REQUIRED_ARTIFACT_NAMES = {
    "selected_token_verification_076a_result.json",
    "latest_selected_token_verification_076a_status.json",
    "selected_token_verification_076a_evidence.json",
    "selected_token_verification_076a_operator_summary.md",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/selected_token_verification_models.py"),
    Path("pm_bot/trading_core/selected_token_verification_bridge.py"),
    Path("pm_bot/operator_runner/selected_token_verification_bridge.py"),
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


def _write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_selected_candidate_artifact(
    root: Path,
    *,
    token_id: str = RAW_TOKEN_ID_1,
    candidate_index: int = 0,
    selected_by_operator: bool = True,
    source_backed: bool = True,
    market: str = "BTC",
    strategy: str = "tiny-momentum",
    outcome_label: str = "Yes",
) -> Path:
    return _write_json(
        root / "selected_candidate_artifact_075d" / "selected_candidate_artifact_075d.json",
        {
            "contract_version": "pmbot_selected_candidate_artifact_075d.v1",
            "status": "selected_candidate_artifact_recorded",
            "market_symbol": market,
            "strategy_name": strategy,
            "candidate_index": candidate_index,
            "candidate_id": f"candidate-076a-{candidate_index}",
            "market_title": "Will BTC close above the local review threshold?",
            "market_slug": "btc-up-or-down-076a",
            "outcome_label": outcome_label,
            "outcome_index": candidate_index,
            "token_id_short": "123456...0761",
            "token_id_hash": hashlib.sha256(token_id.encode("utf-8")).hexdigest(),
            "source_ids": ["operator_token_selection_packet_073b"],
            "source_paths": ["pm_bot/trading_core/artifacts/operator_token_selection_packet_073b/operator_token_selection_candidates_073b.json"],
            "selected_by_operator": selected_by_operator,
            "source_backed": source_backed,
            "selected_candidate_executable_for_live": False,
            "selected_candidate_submit_ready": False,
            "allowed_for_live": False,
            "token_id_generated": False,
            "fake_token_id_generated": False,
            "order_payload_generated": False,
            "signed_payload_generated": False,
            "order_submission_enabled": False,
            "order_cancellation_enabled": False,
            "private_key_read": False,
        },
    )


def _write_073b_candidates(root: Path, *, tokens: list[str] | None = None) -> Path:
    token_values = tokens if tokens is not None else [RAW_TOKEN_ID_1, RAW_TOKEN_ID_2]
    return _write_json(
        root / "operator_token_selection_packet_073b" / "operator_token_selection_candidates_073b.json",
        {
            "contract_version": "pmbot_operator_token_selection_candidates_073b.v1",
            "status": "selection_required",
            "market_symbol": "BTC",
            "strategy_name": "tiny-momentum",
            "candidate_index_base": 0,
            "source_backed_candidate_count": len(token_values),
            "source_backed_candidates": [
                {
                    "candidate_index": index,
                    "candidate_id": f"candidate-076a-{index}",
                    "market_slug": "btc-up-or-down-076a",
                    "question": "Will BTC close above the local review threshold?",
                    "outcome_name": "Yes" if index == 0 else "No",
                    "outcome_index": index,
                    "token_id": token_id,
                    "source_ids": ["public_market_token_discovery_071a"],
                    "source_paths": ["pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_market_token_discovery_071a_result.json"],
                    "source_backed": True,
                    "token_id_source_backed": True,
                    "token_id_generated": False,
                    "fake_token_id_generated": False,
                    "operator_selectable": True,
                    "allowed_for_live": False,
                }
                for index, token_id in enumerate(token_values)
            ],
            "allowed_for_live": False,
            "review_only": True,
            "dry_run_only": True,
        },
    )


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


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
    for row in _walk_mappings(value):
        for field in REQUIRED_FALSE_FLAGS:
            if field in row:
                assert row[field] is False, field
        if "resolved_blocker_count" in row:
            assert row["resolved_blocker_count"] == 0


def test_missing_selected_candidate_artifact_blocks_without_live_readiness(tmp_path: Path) -> None:
    _write_073b_candidates(tmp_path / "sources")

    result = run_selected_token_verification_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE_ARTIFACT
    assert result["selected_candidate_artifact_present"] is False
    assert result["selected_token_verified_for_payload_dry_run"] is False
    assert result["selected_token_payload_ready_for_submit"] is False
    assert result["allowed_for_live"] is False
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_selected_candidate_matches_source_backed_073b_candidate_without_raw_token_output(tmp_path: Path) -> None:
    _write_selected_candidate_artifact(tmp_path / "sources")
    _write_073b_candidates(tmp_path / "sources")

    result = run_selected_token_verification_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    paths = selected_token_verification_artifact_paths(tmp_path / "out")
    artifact_text = _artifact_text(paths)
    keys = set(_walk_keys(result))

    assert result["status"] == STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN
    assert result["selected_candidate_artifact_present"] is True
    assert result["selected_candidate_index"] == 0
    assert result["selected_by_operator"] is True
    assert result["source_backed"] is True
    assert result["token_hash_match"] is True
    assert result["token_short_match"] is True
    assert result["market_match"] is True
    assert result["strategy_match"] is True
    assert result["market_title_match"] is True
    assert result["outcome_label_match"] is True
    assert result["selected_candidate_in_known_candidate_set"] is True
    assert result["selected_token_verified_for_payload_dry_run"] is True
    assert result["selected_token_payload_ready_for_submit"] is False
    assert result["allowed_for_live"] is False
    assert set(p.name for p in (tmp_path / "out").iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert RAW_TOKEN_ID_1 not in artifact_text
    assert RAW_TOKEN_ID_2 not in artifact_text
    assert not (keys & {"token_id", "selected_token_id", "outcome_token_id", "signed_payload", "signed_order"})
    assert validate_selected_token_verification_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_selected_candidate_not_in_source_backed_set_blocks(tmp_path: Path) -> None:
    _write_selected_candidate_artifact(tmp_path / "sources", token_id=RAW_TOKEN_ID_1)
    _write_073b_candidates(tmp_path / "sources", tokens=[RAW_TOKEN_ID_2])

    result = run_selected_token_verification_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_BLOCKED_SELECTED_TOKEN_NOT_SOURCE_VERIFIED
    assert result["selected_candidate_artifact_present"] is True
    assert result["token_hash_match"] is False
    assert result["selected_candidate_in_known_candidate_set"] is False
    assert result["selected_token_verified_for_payload_dry_run"] is False
    assert result["allowed_for_live"] is False
    assert "token_hash_match" in {row["blocker_id"] for row in result["blockers"]}
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_readiness_gate_consumes_verification_bridge_and_progresses_to_next_blocker(tmp_path: Path) -> None:
    selected_path = _write_selected_candidate_artifact(tmp_path / "sources")
    selection_path = _write_073b_candidates(tmp_path / "sources")
    bridge = run_selected_token_verification_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "bridge_out",
        generated_at=GENERATED_AT,
    )
    result = run_selected_token_payload_readiness_gate(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        selected_candidate_artifact_path=selected_path,
        operator_token_selection_packet_path=selection_path,
        selected_token_verification_bridge_path=selected_token_verification_artifact_paths(tmp_path / "bridge_out")["result"],
        first_order_market_token_contract_path=tmp_path / "missing_resolver.json",
        signer_diagnostic_evidence_path=tmp_path / "missing_signer_evidence.json",
        approval_contract_status_path=tmp_path / "missing_approval.json",
        signed_payload_dry_run_status_path=tmp_path / "missing_dry_run.json",
        signed_payload_diagnostic_adapter_status_path=tmp_path / "missing_adapter.json",
        artifact_dir=tmp_path / "readiness_out",
        generated_at=GENERATED_AT,
    )
    selected_token = result["readiness_summaries"]["selected_token"]

    assert bridge["status"] == STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN
    assert result["status"] == STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC_EVIDENCE
    assert result["status"] != STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN
    assert selected_token["selected_token_verified"] is True
    assert selected_token["selected_token_verification_bridge_verified"] is True
    assert result["latest_status"]["selected_token_verification_bridge_verified"] is True
    assert result["selected_token_payload_ready_for_submit"] is False
    assert result["allowed_for_live"] is False


def test_runner_emits_required_artifacts_only_and_rejects_token_or_live_flags(tmp_path: Path) -> None:
    _write_selected_candidate_artifact(tmp_path / "sources")
    _write_073b_candidates(tmp_path / "sources")
    out_dir = tmp_path / "cli_out"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.selected_token_verification_bridge",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifact-root",
            str(tmp_path / "sources"),
            "--artifacts-dir",
            str(out_dir),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    forbidden = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.selected_token_verification_bridge",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--token-id",
            RAW_TOKEN_ID_1,
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = json.loads(selected_token_verification_artifact_paths(out_dir)["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Selected token verification bridge 076A completed." in completed.stdout
    assert "Status: selected_token_verified_for_payload_dry_run" in completed.stdout
    assert "Selected token payload ready for submit: false" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert set(p.name for p in out_dir.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert result["selected_token_verified_for_payload_dry_run"] is True
    assert result["selected_token_payload_ready_for_submit"] is False
    assert result["allowed_for_live"] is False
    assert forbidden.returncode != 0
    assert "unsupported live/auth/wallet/sign/order/write/browser/token flag" in forbidden.stderr
    _assert_required_false_flags(result)


def test_no_network_order_signing_secret_browser_or_background_runtime_calls_exist() -> None:
    source = (
        inspect.getsource(bridge_module)
        + "\n"
        + inspect.getsource(models_module)
        + "\n"
        + inspect.getsource(runner_module)
    ).lower()
    forbidden_terms = (
        "requests.",
        "httpx.",
        "urllib.request",
        "selenium",
        "playwright",
        ".post(",
        ".put(",
        ".patch(",
        ".delete(",
        "py_clob_client",
        "clobclient",
        "eth_account",
        "web3",
        "account.from_key",
        ".sign(",
        "sign_typed_data",
        "eip712",
        "create_order(",
        "post_order(",
        "submit_order(",
        "place_order(",
        "send_order(",
        "execute_order(",
        "cancel_order(",
        "delete_order(",
        "submit_cancel(",
        "while true",
        "time.sleep",
        "threading",
        "asyncio",
        "sched.",
        "start-process",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.", "start-process")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert term not in lowered, path
