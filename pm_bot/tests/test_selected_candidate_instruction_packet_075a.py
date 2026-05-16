from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.operator_runner.selected_candidate_instruction_packet as runner_module
import pm_bot.trading_core.selected_candidate_instruction_models as models_module
import pm_bot.trading_core.selected_candidate_instruction_packet as packet_module
from pm_bot.trading_core.selected_candidate_instruction_models import (
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_MISSING_SOURCE_BACKED_CANDIDATES,
    STATUS_OPERATOR_SELECTION_REQUIRED,
    validate_selected_candidate_instruction_result,
)
from pm_bot.trading_core.selected_candidate_instruction_packet import (
    run_selected_candidate_instruction_packet,
    selected_candidate_instruction_artifact_paths,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"
RAW_TOKEN_ID_1 = "123456789012345678900751"
RAW_TOKEN_ID_2 = "123456789012345678900752"

REQUIRED_ARTIFACT_NAMES = {
    "selected_candidate_instruction_packet_075a_result.json",
    "latest_selected_candidate_instruction_packet_075a.json",
    "selected_candidate_instruction_candidates_075a.json",
    "selected_candidate_instruction_packet_075a.json",
    "selected_candidate_instruction_packet_075a.md",
    "selected_candidate_instruction_safety_snapshot_075a.json",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/selected_candidate_instruction_models.py"),
    Path("pm_bot/trading_core/selected_candidate_instruction_packet.py"),
    Path("pm_bot/operator_runner/selected_candidate_instruction_packet.py"),
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


def _write_073b_candidates(root: Path, *, tokens: list[str] | None = None) -> None:
    token_values = tokens if tokens is not None else [RAW_TOKEN_ID_1, RAW_TOKEN_ID_2]
    _write_json(
        root / "operator_token_selection_packet_073b" / "operator_token_selection_candidates_073b.json",
        {
            "contract_version": "pmbot_operator_token_selection_candidates_073b.v1",
            "status": "selection_required",
            "candidate_index_base": 0,
            "source_backed_candidate_count": len(token_values),
            "source_backed_candidates": [
                {
                    "candidate_index": index,
                    "candidate_id": f"candidate-075a-{index}",
                    "market_slug": "btc-up-or-down-075a",
                    "question": "Will BTC close above the local review threshold?",
                    "outcome_name": "Yes" if index == 0 else "No",
                    "outcome_index": index,
                    "token_id": token_id,
                    "source_ids": ["public_market_token_discovery_071a"],
                    "source_paths": [
                        "pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_market_token_discovery_071a_result.json"
                    ],
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


def test_no_candidates_blocks_without_inventing_or_selecting_token(tmp_path: Path) -> None:
    result = run_selected_candidate_instruction_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "missing_sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_BLOCKED_MISSING_SOURCE_BACKED_CANDIDATES
    assert result["source_backed_candidate_count"] == 0
    assert result["operator_selection_required"] is False
    assert result["selected_token_id_present"] is False
    assert result["selected_candidate_artifact_written"] is False
    assert result["selected_token_artifact_written"] is False
    assert result["instruction_packet_executable_for_live"] is False
    assert result["allowed_for_live"] is False
    assert validate_selected_candidate_instruction_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_multiple_candidates_remain_operator_selection_required_without_auto_pick(tmp_path: Path) -> None:
    _write_073b_candidates(tmp_path / "sources")

    result = run_selected_candidate_instruction_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    artifact_text = _artifact_text(selected_candidate_instruction_artifact_paths(tmp_path / "out"))

    assert result["status"] == STATUS_OPERATOR_SELECTION_REQUIRED
    assert result["source_backed_candidate_count"] == 2
    assert result["operator_selection_required"] is True
    assert result["requested_candidate_available"] is False
    assert result["source_backed_candidates"][0]["candidate_index"] == 0
    assert result["source_backed_candidates"][0]["market_title"] == "Will BTC close above the local review threshold?"
    assert result["source_backed_candidates"][0]["outcome_label"] == "Yes"
    assert result["source_backed_candidates"][0]["token_id_short"] == "123456...0751"
    assert "--candidate-index 0" in result["source_backed_candidates"][0]["safe_cli_command"]
    assert "--candidate-index 1" in result["source_backed_candidates"][1]["safe_cli_command"]
    assert RAW_TOKEN_ID_1 not in artifact_text
    assert RAW_TOKEN_ID_2 not in artifact_text
    assert "operator_selection_required" in {row["blocker_id"] for row in result["blockers"]}
    assert validate_selected_candidate_instruction_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_candidate_index_only_renders_concrete_instruction_and_does_not_select(tmp_path: Path) -> None:
    _write_073b_candidates(tmp_path / "sources")

    result = run_selected_candidate_instruction_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        candidate_index=1,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_OPERATOR_SELECTION_REQUIRED
    assert result["requested_candidate_available"] is True
    assert result["requested_candidate_preview"]["candidate_index"] == 1
    assert result["safe_cli_command_for_requested_candidate"].endswith("--candidate-index 1")
    assert result["selected_token_id_present"] is False
    assert result["selected_candidate_artifact_written"] is False
    assert result["selection_artifact_write_performed"] is False
    assert result["operator_selection_applied"] is False
    assert validate_selected_candidate_instruction_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_invalid_candidate_index_stays_review_instruction_packet(tmp_path: Path) -> None:
    _write_073b_candidates(tmp_path / "sources")

    result = run_selected_candidate_instruction_packet(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        candidate_index=9,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_OPERATOR_SELECTION_REQUIRED
    assert result["requested_candidate_available"] is False
    assert "requested_candidate_index_unavailable" in {row["blocker_id"] for row in result["blockers"]}
    assert result["selected_token_id_present"] is False
    assert result["safe_cli_command_for_requested_candidate"] == ""
    assert validate_selected_candidate_instruction_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_runner_emits_required_artifacts_only_and_shortens_token_ids(tmp_path: Path) -> None:
    _write_073b_candidates(tmp_path / "sources")
    out_dir = tmp_path / "cli_out"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.selected_candidate_instruction_packet",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--candidate-index",
            "0",
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
    paths = selected_candidate_instruction_artifact_paths(out_dir)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    keys = set(_walk_keys(result))
    artifact_text = _artifact_text(paths)

    assert completed.returncode == 0, completed.stderr
    assert "Selected candidate instruction packet 075A completed." in completed.stdout
    assert "Status: operator_selection_required" in completed.stdout
    assert "Selected token id present: false" in completed.stdout
    assert "Selected candidate artifact written: false" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Instruction packet executable for live: false" in completed.stdout
    assert set(p.name for p in out_dir.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert not (keys & {"token_id", "selected_token_id", "outcome_token_id", "signed_payload", "signed_order"})
    assert "123456...0751" in artifact_text
    assert RAW_TOKEN_ID_1 not in artifact_text
    assert RAW_TOKEN_ID_2 not in artifact_text
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_runner_requires_dry_run_and_rejects_live_token_flags(tmp_path: Path) -> None:
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.selected_candidate_instruction_packet",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--artifacts-dir",
            str(tmp_path / "missing_dry_run"),
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
            "pm_bot.operator_runner.selected_candidate_instruction_packet",
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

    assert missing_dry_run.returncode != 0
    assert "requires --dry-run" in missing_dry_run.stderr
    assert forbidden.returncode != 0
    assert "unsupported live/auth/wallet/sign/order/write/browser/token flag" in forbidden.stderr


def test_no_network_order_signing_secret_browser_or_background_runtime_calls_exist() -> None:
    source = (
        inspect.getsource(packet_module)
        + "\n"
        + inspect.getsource(models_module)
        + "\n"
        + inspect.getsource(runner_module)
    ).lower()
    forbidden_terms = (
        "os.environ",
        "getenv",
        "environ[",
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
