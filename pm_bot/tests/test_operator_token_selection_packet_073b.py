from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.trading_core.operator_token_selection_models as models_module
import pm_bot.trading_core.operator_token_selection_packet as packet_module
from pm_bot.trading_core.operator_token_selection_models import (
    REQUIRED_FALSE_FLAGS,
    STATUS_INVALID_SELECTION,
    STATUS_NO_CANDIDATES,
    STATUS_SELECTED_OPERATOR_UNVERIFIED,
    STATUS_SELECTED_SOURCE_BACKED,
    STATUS_SELECTION_REQUIRED,
    validate_operator_token_selection_result,
)
from pm_bot.trading_core.operator_token_selection_packet import (
    operator_token_selection_artifact_paths,
    run_operator_token_selection_packet,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"
TOKEN_ID = "123456789012345678900731"
SECOND_TOKEN_ID = "123456789012345678900732"
MANUAL_TOKEN_ID = "123456789012345678900799"
VALID_CONDITION_ID = "0x" + ("a" * 64)

REQUIRED_ARTIFACT_NAMES = {
    "operator_token_selection_packet_073b_result.json",
    "latest_operator_token_selection_status_073b.json",
    "operator_token_selection_candidates_073b.json",
    "operator_token_selection_packet_073b.json",
    "operator_token_selection_instructions_073b.md",
    "operator_token_selection_safety_snapshot_073b.json",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/operator_token_selection_models.py"),
    Path("pm_bot/trading_core/operator_token_selection_packet.py"),
    Path("pm_bot/operator_runner/operator_token_selection_packet.py"),
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


def _write_source_artifacts(root: Path, *, tokens: list[str] | None = None) -> None:
    token_values = tokens if tokens is not None else [TOKEN_ID, SECOND_TOKEN_ID]
    discovery_candidates = [
        {
            "token_candidate_id": f"token-candidate-073b-{index}",
            "market_candidate_id": "market-candidate-073b",
            "market_id": VALID_CONDITION_ID,
            "market_slug": "bitcoin-up-or-down-073b",
            "question": "Will Bitcoin be above the public threshold?",
            "outcome_name": "Yes" if index == 0 else "No",
            "outcome_index": index,
            "token_id": token_id,
            "source_name": "public_gamma_live_read_only",
            "source_type": "public_gamma_read_only",
            "source_origin": "public_network",
            "source_path": "/events",
            "source_backed": True,
            "token_id_is_source_backed": True,
            "token_id_is_generated": False,
            "source_payload_hash": "hash-073b",
        }
        for index, token_id in enumerate(token_values)
    ]
    _write_json(
        root / "public_market_token_discovery_071a" / "public_market_token_discovery_071a_result.json",
        {
            "contract_version": "pmbot_public_market_token_discovery_result_071a.v1",
            "status": "source_backed_candidates_ready" if token_values else "no_source_backed_candidates",
            "market": "BTC",
            "strategy": "tiny-momentum",
            "market_candidates": [
                {
                    "market_candidate_id": "market-candidate-073b",
                    "market_id": VALID_CONDITION_ID,
                    "market_slug": "bitcoin-up-or-down-073b",
                    "question": "Will Bitcoin be above the public threshold?",
                    "source_backed": True,
                    "source_payload_hash": "hash-073b",
                }
            ],
            "outcome_token_candidates": discovery_candidates,
            "generated_at": GENERATED_AT,
            "dry_run": True,
            "allowed_for_live": False,
        },
    )
    _write_json(
        root / "discovery_to_token_resolver_bridge_071d" / "discovery_to_token_resolver_bridge_071d_result.json",
        {
            "contract_version": "pmbot_discovery_to_token_resolver_bridge_071d_result.v1",
            "status": "operator_selection_required_multiple_source_backed_candidates",
            "operator_selection_required": {"selection_required": len(token_values) > 1},
            "valid_source_backed_candidates": [
                {
                    "bridge_candidate_id": f"bridge-candidate-073b-{index}",
                    "source_token_candidate_id": f"token-candidate-073b-{index}",
                    "market_candidate_id": "market-candidate-073b",
                    "market_id": VALID_CONDITION_ID,
                    "market_slug": "bitcoin-up-or-down-073b",
                    "question": "Will Bitcoin be above the public threshold?",
                    "outcome_name": "Yes" if index == 0 else "No",
                    "outcome_index": index,
                    "token_id": token_id,
                    "source_backed": True,
                    "token_id_source_backed": True,
                    "token_id_generated": False,
                }
                for index, token_id in enumerate(token_values)
            ],
            "generated_at": GENERATED_AT,
            "allowed_for_live": False,
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


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key == "root":
            continue
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_no_candidates_blocks_without_inventing_token_id(tmp_path: Path) -> None:
    result = run_operator_token_selection_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "missing",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_NO_CANDIDATES
    assert result["source_backed_candidate_count"] == 0
    assert result["selected_token_id"] == ""
    assert result["selected_token_id_present"] is False
    assert result["token_id_generated"] is False
    assert result["fake_token_id_generated"] is False
    assert validate_operator_token_selection_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_multiple_candidates_require_selection_and_do_not_auto_pick(tmp_path: Path) -> None:
    _write_source_artifacts(tmp_path / "sources")

    result = run_operator_token_selection_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_SELECTION_REQUIRED
    assert result["source_backed_candidate_count"] == 2
    assert result["selected_token_id"] == ""
    assert result["operator_selection_required"] is True
    assert result["auto_selected_for_live"] is False
    assert "operator_selection_required" in {row["blocker_id"] for row in result["blockers"]}
    assert validate_operator_token_selection_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_candidate_index_selects_only_source_backed_candidate(tmp_path: Path) -> None:
    _write_source_artifacts(tmp_path / "sources")

    result = run_operator_token_selection_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        candidate_index=1,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    selection = result["selection"]

    assert result["status"] == STATUS_SELECTED_SOURCE_BACKED
    assert result["selected_token_id"] == SECOND_TOKEN_ID
    assert result["selected_token_source_backed"] is True
    assert selection["selected_candidate_index"] == 1
    assert selection["selected_candidate"]["source_backed"] is True
    assert result["packet"]["safe_next_cli"]["first_order_market_token_resolver_070b"]
    assert validate_operator_token_selection_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_invalid_candidate_index_blocks(tmp_path: Path) -> None:
    _write_source_artifacts(tmp_path / "sources")

    result = run_operator_token_selection_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        candidate_index=9,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_INVALID_SELECTION
    assert result["selected_token_id"] == ""
    assert "candidate_index_out_of_range" in {row["blocker_id"] for row in result["blockers"]}
    assert validate_operator_token_selection_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_manual_token_id_is_format_validated_and_unverified_unless_matching_source_candidate(tmp_path: Path) -> None:
    _write_source_artifacts(tmp_path / "sources")

    unverified = run_operator_token_selection_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_id=MANUAL_TOKEN_ID,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out_unverified",
        generated_at=GENERATED_AT,
    )
    matching = run_operator_token_selection_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_id=TOKEN_ID,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out_matching",
        generated_at=GENERATED_AT,
    )
    invalid = run_operator_token_selection_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_id="not-a-decimal-token",
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out_invalid",
        generated_at=GENERATED_AT,
    )

    assert unverified["status"] == STATUS_SELECTED_OPERATOR_UNVERIFIED
    assert unverified["selected_token_id"] == MANUAL_TOKEN_ID
    assert unverified["operator_provided"] is True
    assert unverified["operator_provided_unverified"] is True
    assert unverified["selected_token_source_backed"] is False
    assert matching["status"] == STATUS_SELECTED_SOURCE_BACKED
    assert matching["selected_token_id"] == TOKEN_ID
    assert matching["operator_provided"] is True
    assert matching["selected_token_source_backed"] is True
    assert invalid["status"] == STATUS_INVALID_SELECTION
    assert invalid["selected_token_id"] == ""
    assert invalid["selection"]["token_id_format_status"] == "invalid"
    assert validate_operator_token_selection_result(unverified)["valid"] is True
    assert validate_operator_token_selection_result(matching)["valid"] is True
    assert validate_operator_token_selection_result(invalid)["valid"] is True
    _assert_required_false_flags(unverified)
    _assert_required_false_flags(matching)
    _assert_required_false_flags(invalid)


def test_no_fake_token_ids_are_emitted_or_persisted(tmp_path: Path) -> None:
    _write_source_artifacts(tmp_path / "sources", tokens=["fake-token-id-073b", "fixture-token-id-073b"])

    result = run_operator_token_selection_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        token_id="fake-token-id-073b",
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    artifact_text = _artifact_text(operator_token_selection_artifact_paths(tmp_path / "out"))

    assert result["status"] == STATUS_INVALID_SELECTION
    assert result["source_backed_candidate_count"] == 0
    assert result["selected_token_id"] == ""
    assert "fake-token-id-073b" not in artifact_text
    assert "fixture-token-id-073b" not in artifact_text
    assert result["token_id_generated"] is False
    assert result["fake_token_id_generated"] is False


def test_no_order_generation_signing_submit_cancel_or_auth_runtime_calls_exist() -> None:
    source = (
        inspect.getsource(packet_module)
        + "\n"
        + inspect.getsource(models_module)
        + "\n"
        + Path("pm_bot/operator_runner/operator_token_selection_packet.py").read_text(encoding="utf-8")
    ).lower()
    forbidden_terms = (
        "os.environ",
        "getenv",
        "environ[",
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
        "requests.",
        "httpx.",
        "urllib.request",
        "selenium",
        "playwright",
    )

    for term in forbidden_terms:
        assert term not in source, term


def test_allowed_for_live_and_token_selection_executable_remain_false(tmp_path: Path) -> None:
    _write_source_artifacts(tmp_path / "sources")

    result = run_operator_token_selection_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        candidate_index=0,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["allowed_for_live"] is False
    assert result["token_selection_executable"] is False
    assert result["packet"]["allowed_for_live"] is False
    assert result["packet"]["token_selection_executable"] is False
    assert result["latest_status"]["allowed_for_live"] is False
    assert result["latest_status"]["token_selection_executable"] is False
    assert result["order_payload_generated"] is False
    assert result["signing_attempted"] is False
    assert result["order_submission_attempted"] is False
    assert result["order_cancellation_attempted"] is False
    assert result["authenticated_trading_call_performed"] is False
    _assert_required_false_flags(result)


def test_runner_emits_required_artifacts_only(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.operator_token_selection_packet",
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
    paths = operator_token_selection_artifact_paths(tmp_path / "out")
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    keys = set(_walk_keys(result))

    assert completed.returncode == 0, completed.stderr
    assert "Operator token selection packet 073B completed." in completed.stdout
    assert "Status: no_candidates" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Token selection executable: false" in completed.stdout
    assert set(p.name for p in (tmp_path / "out").iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert not (keys & {"order_id", "client_order_id", "signed_payload", "signed_order"})
    assert result["status"] == STATUS_NO_CANDIDATES
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.", "start-process")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert term not in lowered, path
