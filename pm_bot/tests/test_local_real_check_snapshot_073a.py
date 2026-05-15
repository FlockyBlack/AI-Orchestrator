from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.operator_runner.local_real_check_snapshot as runner_module
import pm_bot.trading_core.local_real_check_snapshot as snapshot_module
import pm_bot.trading_core.local_real_check_snapshot_models as models_module
from pm_bot.trading_core.local_real_check_snapshot import (
    local_real_check_snapshot_artifact_paths,
    run_local_real_check_snapshot,
)
from pm_bot.trading_core.local_real_check_snapshot_models import (
    NORMALIZED_STATUS_FIELDS,
    SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C,
    SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D,
    SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D,
    SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A,
    SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C,
    SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C,
    SOURCE_ORDER_PREP_PACKET_072A,
    SOURCE_PUBLIC_MARKET_TOKEN_DISCOVERY_071A,
    SOURCE_SEQUENCE,
    validate_local_real_check_snapshot_result,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"

RAW_SECRET = "raw-secret-073a-never-output"
RAW_PRIVATE_KEY = "0x" + "7" * 64
RAW_ADDRESS = "0x3006000000000000000000000000000000008989"
SHORT_ADDRESS = "0x3006...8989"
FAKE_VALUES = (
    "fake-balance-073a-never-output",
    "fake-order-id-073a-never-output",
    "fake-fill-073a-never-output",
    "fake-pnl-073a-never-output",
    "fake-token-id-073a-never-output",
)

REQUIRED_ARTIFACT_NAMES = {
    "local_real_check_snapshot_073a_result.json",
    "latest_local_real_check_snapshot_status_073a.json",
    "local_real_check_snapshot_sources_073a.json",
    "local_real_check_snapshot_normalized_status_073a.json",
    "local_real_check_snapshot_next_actions_073a.json",
    "local_real_check_snapshot_safety_snapshot_073a.json",
    "local_real_check_snapshot_operator_summary_073a.md",
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


def _write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_source_artifacts(root: Path, *, include_raw_values: bool = False) -> dict[str, Path]:
    extra = {}
    if include_raw_values:
        extra = {
            "private_key": RAW_PRIVATE_KEY,
            "api_secret": RAW_SECRET,
            "wallet_address": RAW_ADDRESS,
            "balance": FAKE_VALUES[0],
            "order_id": FAKE_VALUES[1],
            "fill": FAKE_VALUES[2],
            "pnl": FAKE_VALUES[3],
            "token_id": FAKE_VALUES[4],
        }
    return {
        SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C: _write_json(
            root / "local_real_check_bundle_072c" / "latest_local_real_check_bundle_status_072c.json",
            {
                "contract_version": "fixture.local_real_check_bundle.latest.v1",
                "status": RAW_ADDRESS if include_raw_values else "local_real_check_bundle_completed_with_blockers_live_blocked",
                "allowed_for_live": False,
                **extra,
            },
        ),
        SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C: _write_json(
            root / "clob_l2_auth_readonly_probe_067c" / "latest_clob_l2_auth_readonly_probe_status_067c.json",
            {
                "contract_version": "fixture.clob.latest.v1",
                "status": "authenticated_readonly_probe_succeeded_live_blocked",
                "allowed_for_live": False,
                **extra,
            },
        ),
        SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C: _write_json(
            root / "live_account_readonly_state_probe_070c" / "latest_live_account_readonly_state_status_070c.json",
            {
                "contract_version": "fixture.account.latest.v1",
                "status": "account_state_probe_succeeded_live_blocked",
                "allowed_for_live": False,
                **extra,
            },
        ),
        SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A: _write_json(
            root / "guarded_signer_diagnostic_smoke_069a" / "latest_guarded_signer_diagnostic_status_069a.json",
            {
                "contract_version": "fixture.signer.latest.v1",
                "status": "diagnostic_ok",
                "diagnostic_status": "diagnostic_ok",
                "allowed_for_live": False,
                **extra,
            },
        ),
        SOURCE_PUBLIC_MARKET_TOKEN_DISCOVERY_071A: _write_json(
            root / "public_market_token_discovery_071a" / "latest_public_market_token_discovery_status_071a.json",
            {
                "contract_version": "fixture.discovery.latest.v1",
                "status": "source_backed_candidates_ready",
                "allowed_for_live": False,
                **extra,
            },
        ),
        SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D: _write_json(
            root / "discovery_to_token_resolver_bridge_071d" / "latest_discovery_to_token_resolver_bridge_status_071d.json",
            {
                "contract_version": "fixture.bridge.latest.v1",
                "status": "operator_selection_required_multiple_source_backed_candidates",
                "allowed_for_live": False,
                **extra,
            },
        ),
        SOURCE_ORDER_PREP_PACKET_072A: _write_json(
            root / "order_prep_packet_072a" / "latest_order_prep_packet_status_072a.json",
            {
                "contract_version": "fixture.order_prep.latest.v1",
                "status": "blocked_order_prep_packet_not_ready",
                "allowed_for_live": False,
                **extra,
            },
        ),
        SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D: _write_json(
            root / "first_live_order_final_blocker_reducer_072d" / "latest_first_live_order_final_blockers_072d.json",
            {
                "contract_version": "fixture.final_blocker.latest.v1",
                "status": "blocked_remaining_first_live_order_final_blockers",
                "allowed_for_live": False,
                **extra,
            },
        ),
    }


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key != "root" and path.exists():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_missing_artifacts_produce_missing_unknown_not_fake_success(tmp_path: Path) -> None:
    result = run_local_real_check_snapshot(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "missing_sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == "local_real_check_snapshot_recorded_live_blocked"
    assert result["latest_status"]["source_missing_count"] == len(SOURCE_SEQUENCE)
    assert all(result[field] == "missing" for field in NORMALIZED_STATUS_FIELDS)
    assert result["allowed_for_live"] is False
    assert result["snapshot_executable_for_live"] is False
    assert result["validation"]["valid"] is True
    assert validate_local_real_check_snapshot_result(result, generated_at=GENERATED_AT)["valid"] is True
    assert result["fake_success_inferred"] is False
    assert result["fake_evidence_generated"] is False


def test_normalizes_existing_artifact_statuses_and_paths_safely(tmp_path: Path) -> None:
    source_paths = _write_source_artifacts(tmp_path / "sources")
    result = run_local_real_check_snapshot(
        market="btc",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    sources = result["sources"]["sources"]

    assert result["market"] == "BTC"
    assert result["l2_auth_status"] == "authenticated_readonly_probe_succeeded_live_blocked"
    assert result["account_readonly_status"] == "account_state_probe_succeeded_live_blocked"
    assert result["signer_diagnostic_status"] == "diagnostic_ok"
    assert result["public_discovery_status"] == "source_backed_candidates_ready"
    assert result["token_bridge_status"] == "operator_selection_required_multiple_source_backed_candidates"
    assert result["order_prep_packet_status"] == "blocked_order_prep_packet_not_ready"
    assert result["final_blocker_status"] == "blocked_remaining_first_live_order_final_blockers"
    for source_id, source_path in source_paths.items():
        assert sources[source_id]["exists"] is True
        assert sources[source_id]["parsed"] is True
        assert sources[source_id]["selected_path"].endswith(source_path.name)
        assert sources[source_id]["file_modified_at"]
        assert sources[source_id]["candidate_paths"]


def test_reads_only_known_local_artifact_paths(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    artifact_root = tmp_path / "sources"
    _write_source_artifacts(artifact_root)
    original_load_json_object = snapshot_module.load_json_object
    reads: list[Path] = []

    def guarded_load_json_object(path: str | Path, *, label: str = "input") -> dict[str, Any]:
        path_obj = Path(path).resolve()
        assert path_obj.is_relative_to(artifact_root.resolve())
        reads.append(path_obj)
        return original_load_json_object(path, label=label)

    monkeypatch.setattr(snapshot_module, "load_json_object", guarded_load_json_object)
    run_local_real_check_snapshot(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=artifact_root,
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert {path.parent.name for path in reads} == set(SOURCE_SEQUENCE)
    assert all(path.name.startswith("latest_") for path in reads)


def test_does_not_emit_raw_secret_addresses_or_fake_execution_values(tmp_path: Path) -> None:
    _write_source_artifacts(tmp_path / "sources", include_raw_values=True)
    result = run_local_real_check_snapshot(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    paths = local_real_check_snapshot_artifact_paths(tmp_path / "out")
    rendered = json.dumps(result, sort_keys=True) + "\n" + _artifact_text(paths)

    assert RAW_SECRET not in rendered
    assert RAW_PRIVATE_KEY not in rendered
    assert RAW_ADDRESS not in rendered
    assert SHORT_ADDRESS in rendered
    for fake_value in FAKE_VALUES:
        assert fake_value not in rendered
    assert result["sources"]["sources"][SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C]["status"] == SHORT_ADDRESS
    assert result["raw_source_payloads_embedded"] is False


def test_runner_emits_required_artifacts_only_and_no_secret_output(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.local_real_check_snapshot",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifact-root",
            str(tmp_path / "missing_sources"),
            "--artifacts-dir",
            str(out_dir),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(
            {
                "POLYMARKET_PRIVATE_KEY": RAW_PRIVATE_KEY,
                "POLYMARKET_API_SECRET": RAW_SECRET,
                "POLYMARKET_PASSPHRASE": RAW_SECRET,
            }
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = local_real_check_snapshot_artifact_paths(out_dir)
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Local real-check snapshot 073A completed." in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Snapshot executable for live: false" in completed.stdout
    assert "Network calls: false" in completed.stdout
    assert "Environment secret reads: false" in completed.stdout
    assert "Subchecks run by default: false" in completed.stdout
    assert RAW_PRIVATE_KEY not in completed.stdout
    assert RAW_SECRET not in completed.stdout
    assert set(path.name for path in out_dir.iterdir() if path.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert result["allowed_for_live"] is False
    assert result["snapshot_executable_for_live"] is False


def test_include_latest_artifacts_can_be_disabled(tmp_path: Path) -> None:
    root = tmp_path / "sources"
    _write_source_artifacts(root)
    _write_json(
        root / "clob_l2_auth_readonly_probe_067c" / "clob_l2_auth_readonly_probe_067c_result.json",
        {"status": "result_only_status", "allowed_for_live": False},
    )

    latest_result = run_local_real_check_snapshot(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        include_latest_artifacts=True,
        artifact_root=root,
        artifact_dir=tmp_path / "latest_out",
        generated_at=GENERATED_AT,
    )
    result_only = run_local_real_check_snapshot(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        include_latest_artifacts=False,
        artifact_root=root,
        artifact_dir=tmp_path / "result_out",
        generated_at=GENERATED_AT,
    )

    assert latest_result["l2_auth_status"] == "authenticated_readonly_probe_succeeded_live_blocked"
    assert result_only["l2_auth_status"] == "result_only_status"
    assert result_only["latest_status"]["include_latest_artifacts"] is False


def test_cli_requires_dry_run_and_rejects_forbidden_runtime_flags(tmp_path: Path) -> None:
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.local_real_check_snapshot",
            "--market",
            "BTC",
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
            "pm_bot.operator_runner.local_real_check_snapshot",
            "--market",
            "BTC",
            "--dry-run",
            "--submit",
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
    assert "unsupported live/auth/wallet/sign/order/write flag" in forbidden.stderr


def test_no_env_secret_network_submit_cancel_signing_or_browser_runtime_calls_exist() -> None:
    source = "\n".join(
        [
            inspect.getsource(snapshot_module),
            inspect.getsource(models_module),
            inspect.getsource(runner_module),
        ]
    ).lower()
    forbidden_terms = (
        "os.environ",
        "getenv(",
        "load_dotenv",
        "requests.",
        "httpx.",
        "urllib.request",
        "socket.",
        "websocket",
        "selenium",
        "playwright",
        "py_clob_client",
        "clobclient",
        "eth_account",
        "web3",
        "account.from_key",
        "time.sleep(",
        "threading",
        "asyncio",
        "sched.",
        "start-process",
    )
    for term in forbidden_terms:
        assert term not in source, term
    forbidden_call_patterns = (
        r"\bcreate_order\s*\(",
        r"\bpost_order\s*\(",
        r"\bsubmit_order\s*\(",
        r"\bplace_order\s*\(",
        r"\bsend_order\s*\(",
        r"\bexecute_order\s*\(",
        r"\bcancel_order\s*\(",
        r"\bdelete_order\s*\(",
        r"\bcancel_all_orders\s*\(",
        r"\bsign_order\s*\(",
        r"\bsign_payload\s*\(",
        r"\bgenerate_signed_payload\s*\(",
        r"\bcreate_signed_order\s*\(",
        r"\bconnect_wallet\s*\(",
        r"\.post\s*\(",
        r"\.put\s*\(",
        r"\.patch\s*\(",
        r"\.delete\s*\(",
    )
    for pattern in forbidden_call_patterns:
        assert re.search(pattern, source) is None, pattern
