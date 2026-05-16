from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.operator_runner.selected_candidate_artifact as runner_module
import pm_bot.trading_core.selected_candidate_artifact as artifact_module
import pm_bot.trading_core.selected_candidate_artifact_models as models_module
from pm_bot.trading_core.selected_candidate_artifact import (
    run_selected_candidate_artifact,
    selected_candidate_artifact_paths,
)
from pm_bot.trading_core.selected_candidate_artifact_models import (
    EXPLICIT_WARNINGS,
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_CANDIDATE_NOT_SOURCE_BACKED,
    STATUS_BLOCKED_INVALID_CANDIDATE_INDEX,
    STATUS_OPERATOR_SELECTION_REQUIRED,
    STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED,
    validate_selected_candidate_artifact_result,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"
RAW_TOKEN_ID_1 = "123456789012345678900751"
RAW_TOKEN_ID_2 = "123456789012345678900752"

REQUIRED_ARTIFACT_NAMES_AFTER_SELECTION = {
    "selected_candidate_artifact_075d_result.json",
    "latest_selected_candidate_artifact_075d.json",
    "selected_candidate_artifact_075d.json",
    "selected_candidate_artifact_source_snapshot_075d.json",
    "selected_candidate_artifact_safety_snapshot_075d.json",
    "selected_candidate_artifact_075d.md",
}

RUNTIME_FILES = (
    Path("pm_bot/trading_core/selected_candidate_artifact_models.py"),
    Path("pm_bot/trading_core/selected_candidate_artifact.py"),
    Path("pm_bot/operator_runner/selected_candidate_artifact.py"),
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


def _write_073b_candidates(
    root: Path,
    *,
    tokens: list[str] | None = None,
    source_backed: bool = True,
) -> None:
    token_values = tokens if tokens is not None else [RAW_TOKEN_ID_1, RAW_TOKEN_ID_2]
    _write_json(
        root / "operator_token_selection_packet_073b" / "operator_token_selection_candidates_073b.json",
        {
            "contract_version": "pmbot_operator_token_selection_candidates_073b.v1",
            "status": "selection_required",
            "candidate_index_base": 0,
            "source_backed_candidate_count": len(token_values) if source_backed else 0,
            "source_backed_candidates": [
                {
                    "candidate_index": index,
                    "candidate_id": f"candidate-075d-{index}",
                    "market_slug": "btc-up-or-down-075d",
                    "question": "Will BTC close above the local review threshold?",
                    "outcome_name": "Yes" if index == 0 else "No",
                    "outcome_index": index,
                    "token_id": token_id,
                    "source_ids": ["public_market_token_discovery_071a"],
                    "source_paths": [
                        "pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_market_token_discovery_071a_result.json"
                    ],
                    "source_backed": source_backed,
                    "token_id_source_backed": source_backed,
                    "token_id_generated": False,
                    "fake_token_id_generated": False,
                    "operator_selectable": source_backed,
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


def test_missing_candidate_index_requires_operator_selection(tmp_path: Path) -> None:
    _write_073b_candidates(tmp_path / "sources")

    result = run_selected_candidate_artifact(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_OPERATOR_SELECTION_REQUIRED
    assert result["candidate_index_provided"] is False
    assert result["selected_by_operator"] is False
    assert result["selected_candidate_artifact_written"] is False
    assert result["allowed_for_live"] is False
    assert result["explicit_warnings"] == list(EXPLICIT_WARNINGS)
    assert not selected_candidate_artifact_paths(tmp_path / "out")["artifact"].exists()
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_candidate_index_records_source_backed_candidate_without_raw_token_id(tmp_path: Path) -> None:
    _write_073b_candidates(tmp_path / "sources")

    result = run_selected_candidate_artifact(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        candidate_index=0,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    artifact = result["selected_candidate_artifact"]
    paths = selected_candidate_artifact_paths(tmp_path / "out")
    artifact_text = _artifact_text(paths)

    assert result["status"] == STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED
    assert artifact["market"] == "BTC"
    assert artifact["strategy"] == "tiny-momentum"
    assert artifact["candidate_index"] == 0
    assert artifact["market_title"] == "Will BTC close above the local review threshold?"
    assert artifact["outcome_label"] == "Yes"
    assert artifact["token_id_short"] == "123456...0751"
    assert len(artifact["token_id_hash"]) == 64
    assert artifact["source_backed"] is True
    assert artifact["selected_by_operator"] is True
    assert artifact["selected_candidate_executable_for_live"] is False
    assert artifact["allowed_for_live"] is False
    assert artifact["created_at"] == GENERATED_AT
    assert artifact["explicit_warnings"] == list(EXPLICIT_WARNINGS)
    assert RAW_TOKEN_ID_1 not in artifact_text
    assert RAW_TOKEN_ID_2 not in artifact_text
    assert validate_selected_candidate_artifact_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_invalid_candidate_index_blocks(tmp_path: Path) -> None:
    _write_073b_candidates(tmp_path / "sources")

    result = run_selected_candidate_artifact(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        candidate_index=9,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_BLOCKED_INVALID_CANDIDATE_INDEX
    assert result["candidate_index_valid"] is False
    assert result["selected_candidate_artifact_written"] is False
    assert "blocked_invalid_candidate_index" in {row["blocker_id"] for row in result["blockers"]}
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_candidate_not_source_backed_blocks_without_artifact(tmp_path: Path) -> None:
    _write_073b_candidates(tmp_path / "sources", source_backed=False)

    result = run_selected_candidate_artifact(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        candidate_index=0,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_BLOCKED_CANDIDATE_NOT_SOURCE_BACKED
    assert result["requested_candidate_found"] is True
    assert result["selected_candidate_source_backed"] is False
    assert result["selected_candidate_artifact_written"] is False
    assert "blocked_candidate_not_source_backed" in {row["blocker_id"] for row in result["blockers"]}
    assert result["validation"]["valid"] is True
    _assert_required_false_flags(result)


def test_existing_artifact_rerun_stays_recorded_and_live_blocked(tmp_path: Path) -> None:
    _write_073b_candidates(tmp_path / "sources")
    first = run_selected_candidate_artifact(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        candidate_index=1,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    second = run_selected_candidate_artifact(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        candidate_index=1,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert first["status"] == STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED
    assert second["status"] == STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED
    assert second["selected_candidate_artifact_preexisting"] is True
    assert second["allowed_for_live"] is False
    assert second["selected_candidate_artifact"]["allowed_for_live"] is False
    assert second["selected_candidate_artifact"]["token_id_short"] == "123456...0752"
    _assert_required_false_flags(second)


def test_runner_emits_required_artifacts_only_and_no_raw_token_id(tmp_path: Path) -> None:
    _write_073b_candidates(tmp_path / "sources")
    out_dir = tmp_path / "cli_out"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.selected_candidate_artifact",
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
    paths = selected_candidate_artifact_paths(out_dir)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    keys = set(_walk_keys(result))
    artifact_text = completed.stdout + "\n" + _artifact_text(paths)

    assert completed.returncode == 0, completed.stderr
    assert "Selected candidate artifact 075D completed." in completed.stdout
    assert "Status: selected_candidate_artifact_recorded" in completed.stdout
    assert "Selected candidate executable for live: false" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Submit-ready: false" in completed.stdout
    assert set(p.name for p in out_dir.iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES_AFTER_SELECTION
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
            "pm_bot.operator_runner.selected_candidate_artifact",
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
            "pm_bot.operator_runner.selected_candidate_artifact",
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
        inspect.getsource(artifact_module)
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
