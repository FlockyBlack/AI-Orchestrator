from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.operator_runner.real_local_check_evidence_review as runner_module
import pm_bot.trading_core.real_local_check_evidence_review as review_module
import pm_bot.trading_core.real_local_check_evidence_review_models as models_module
from pm_bot.trading_core.real_local_check_evidence_review import (
    real_local_check_evidence_review_artifact_paths,
    run_real_local_check_evidence_review,
)
from pm_bot.trading_core.real_local_check_evidence_review_models import (
    GROUP_IDS,
    validate_real_local_check_evidence_review_result,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"

RAW_SECRET = "raw-secret-074a-never-output"
RAW_PRIVATE_KEY = "0x" + "7" * 64
RAW_ADDRESS = "0x3006000000000000000000000000000000008989"

REQUIRED_ARTIFACT_NAMES = {
    "real_local_check_evidence_review_074a_result.json",
    "latest_real_local_check_evidence_review_status_074a.json",
    "real_local_check_evidence_review_groups_074a.json",
    "real_local_check_evidence_review_blockers_074a.json",
    "real_local_check_evidence_review_safety_snapshot_074a.json",
    "real_local_check_evidence_review_operator_diagnosis_074a.md",
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


def _write_complete_sources(root: Path, *, include_raw_values: bool = False) -> dict[str, Path]:
    extra = {}
    if include_raw_values:
        extra = {
            "private_key": RAW_PRIVATE_KEY,
            "api_secret": RAW_SECRET,
            "wallet_address": RAW_ADDRESS,
            "status_with_secret": f"private_key={RAW_SECRET}",
        }
    return {
        "local_real_check_snapshot_073a": _write_json(
            root / "local_real_check_snapshot_073a" / "latest_local_real_check_snapshot_status_073a.json",
            {
                "contract_version": "fixture.snapshot.latest.v1",
                "status": "local_real_check_snapshot_recorded_live_blocked",
                "l2_auth_status": "authenticated_readonly_probe_succeeded_live_blocked",
                "account_readonly_status": "account_state_probe_succeeded_live_blocked",
                "signer_diagnostic_status": "diagnostic_ok",
                "token_bridge_status": "ready_source_backed_token_contract",
                "allowed_for_live": False,
                **extra,
            },
        ),
        "local_real_check_bundle_072c": _write_json(
            root / "local_real_check_bundle_072c" / "latest_local_real_check_bundle_status_072c.json",
            {
                "contract_version": "fixture.bundle.latest.v1",
                "status": "local_real_check_bundle_completed_with_blockers_live_blocked",
                "subcheck_statuses": {
                    "clob_l2_auth_readonly_probe_067c": "authenticated_readonly_probe_succeeded_live_blocked",
                    "live_account_readonly_state_probe_070c": "account_state_probe_succeeded_live_blocked",
                    "guarded_signer_diagnostic_smoke_069a": "diagnostic_ok",
                },
                "allowed_for_live": False,
                **extra,
            },
        ),
        "clob_l2_auth_readonly_probe_067c": _write_json(
            root / "clob_l2_auth_readonly_probe_067c" / "latest_clob_l2_auth_readonly_probe_status_067c.json",
            {
                "contract_version": "fixture.clob.latest.v1",
                "status": "authenticated_readonly_probe_succeeded_live_blocked",
                "allowed_for_live": False,
                **extra,
            },
        ),
        "live_account_readonly_state_probe_070c": _write_json(
            root / "live_account_readonly_state_probe_070c" / "latest_live_account_readonly_state_status_070c.json",
            {
                "contract_version": "fixture.account.latest.v1",
                "status": "account_state_probe_succeeded_live_blocked",
                "account_status": "account_state_probe_succeeded_live_blocked",
                "balance_allowance_status": "available_redacted",
                "allowed_for_live": False,
                **extra,
            },
        ),
        "guarded_signer_diagnostic_smoke_069a": _write_json(
            root / "guarded_signer_diagnostic_smoke_069a" / "latest_guarded_signer_diagnostic_status_069a.json",
            {
                "contract_version": "fixture.signer.latest.v1",
                "status": "diagnostic_ok",
                "diagnostic_status": "diagnostic_ok",
                "private_key_read": False,
                "allowed_for_live": False,
                **extra,
            },
        ),
        "discovery_to_token_resolver_bridge_071d": _write_json(
            root / "discovery_to_token_resolver_bridge_071d" / "latest_discovery_to_token_resolver_bridge_status_071d.json",
            {
                "contract_version": "fixture.bridge.latest.v1",
                "status": "ready_source_backed_token_contract",
                "target_token_id_present": True,
                "target_token_id_source_backed": True,
                "allowed_for_live": False,
                **extra,
            },
        ),
        "first_order_market_token_resolver_070b": _write_json(
            root / "first_order_market_token_resolver_070b" / "latest_first_order_market_token_status_070b.json",
            {
                "contract_version": "fixture.resolver.latest.v1",
                "status": "first_order_market_token_contract_ready_review_only",
                "token_id_present": True,
                "token_id_format_valid": True,
                "allowed_for_live": False,
                **extra,
            },
        ),
        "operator_token_selection_packet_073b": _write_json(
            root / "operator_token_selection_packet_073b" / "latest_operator_token_selection_status_073b.json",
            {
                "contract_version": "fixture.selection.latest.v1",
                "status": "selected_source_backed_candidate",
                "selected_token_id_present": True,
                "selected_token_source_backed": True,
                "allowed_for_live": False,
                **extra,
            },
        ),
        "selected_token_payload_readiness_gate_073c": _write_json(
            root / "selected_token_payload_readiness_gate_073c" / "latest_selected_token_payload_readiness_status_073c.json",
            {
                "contract_version": "fixture.readiness.latest.v1",
                "status": "ready_for_signed_payload_diagnostic",
                "ready_for_signed_payload_diagnostic": True,
                "selected_token_payload_ready_for_submit": False,
                "allowed_for_live": False,
                **extra,
            },
        ),
        "first_live_order_approval_contract_065d": _write_json(
            root / "first_live_order_approval_contract_065d" / "latest_first_live_order_approval_contract_status_065d.json",
            {
                "contract_version": "fixture.approval.latest.v1",
                "status": "approval_contract_defined_execution_blocked",
                "operator_approval_recorded": False,
                "approval_consumed": False,
                "allowed_for_live": False,
                **extra,
            },
        ),
        "first_live_order_final_blocker_reducer_072d": _write_json(
            root / "first_live_order_final_blocker_reducer_072d" / "latest_first_live_order_final_blockers_072d.json",
            {
                "contract_version": "fixture.final.latest.v1",
                "status": "blocked_remaining_first_live_order_final_blockers",
                "remaining_blocker_count": 3,
                "unknown_group_count": 0,
                "live_execution_authorization": "blocked",
                "signing": "blocked",
                "order_submission": "blocked",
                "order_cancellation": "blocked",
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


def test_complete_local_artifact_review_groups_required_evidence_and_still_blocks(tmp_path: Path) -> None:
    _write_complete_sources(tmp_path / "sources")
    result = run_real_local_check_evidence_review(
        market="btc",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    paths = real_local_check_evidence_review_artifact_paths(tmp_path / "out")
    labels = [row["group_label"] for row in result["groups"]]
    blocker_ids = {row["blocker_id"] for row in result["remaining_blockers"]}

    assert result["market"] == "BTC"
    assert tuple(row["group_id"] for row in result["groups"]) == GROUP_IDS
    assert labels == [
        "L2 credentials/auth",
        "account/balance/allowance",
        "signer/private-key diagnostic",
        "token selection",
        "selected-token payload readiness",
        "approval",
        "final blockers",
    ]
    assert result["status"] == "blocked_first_supervised_tiny_order_not_ready"
    assert result["validation"]["valid"] is True
    assert validate_real_local_check_evidence_review_result(result, generated_at=GENERATED_AT)["valid"] is True
    assert "operator_approval_not_recorded_or_consumed" in blocker_ids
    assert "separate_live_execution_authorization_missing" in blocker_ids
    assert "submit_cancel_signing_forbidden_in_074a" in blocker_ids
    assert result["allowed_for_live"] is False
    assert result["review_executable_for_live"] is False
    assert paths["result"].exists()
    assert set(path.name for key, path in paths.items() if key != "root") == REQUIRED_ARTIFACT_NAMES


def test_missing_snapshot_and_payload_readiness_remain_unknown_without_fake_success(tmp_path: Path) -> None:
    _write_complete_sources(tmp_path / "sources")
    (tmp_path / "sources" / "local_real_check_snapshot_073a" / "latest_local_real_check_snapshot_status_073a.json").unlink()
    readiness = tmp_path / "sources" / "selected_token_payload_readiness_gate_073c" / "latest_selected_token_payload_readiness_status_073c.json"
    readiness.unlink()

    result = run_real_local_check_evidence_review(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    blocker_ids = {row["blocker_id"] for row in result["remaining_blockers"]}

    assert result["validation"]["valid"] is True
    assert "local_real_check_snapshot_073a_missing" in blocker_ids
    assert "selected_token_payload_readiness_gate_073c_missing" in blocker_ids
    assert result["fake_success_inferred"] is False
    assert result["fake_evidence_generated"] is False
    assert result["allowed_for_live"] is False


def test_does_not_emit_raw_secret_values_from_source_artifacts(tmp_path: Path) -> None:
    _write_complete_sources(tmp_path / "sources", include_raw_values=True)
    result = run_real_local_check_evidence_review(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    rendered = json.dumps(result, sort_keys=True) + "\n" + _artifact_text(
        real_local_check_evidence_review_artifact_paths(tmp_path / "out")
    )

    assert RAW_SECRET not in rendered
    assert RAW_PRIVATE_KEY not in rendered
    assert RAW_ADDRESS not in rendered
    for row in _walk_mappings(result):
        assert row.get("raw_source_payload_embedded") is not True
        assert row.get("source_payload_values_embedded") is not True


def test_runner_emits_human_readable_diagnosis_without_secret_output(tmp_path: Path) -> None:
    _write_complete_sources(tmp_path / "sources")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.real_local_check_evidence_review",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifact-root",
            str(tmp_path / "sources"),
            "--artifacts-dir",
            str(tmp_path / "out"),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(
            {
                "POLYMARKET_PRIVATE_KEY": RAW_PRIVATE_KEY,
                "POLYMARKET_API_SECRET": RAW_SECRET,
            }
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    diagnosis = (tmp_path / "out" / "real_local_check_evidence_review_operator_diagnosis_074a.md").read_text(
        encoding="utf-8"
    )

    assert completed.returncode == 0, completed.stderr
    assert "Real local-check evidence review 074A completed." in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Live execution authorization: blocked" in completed.stdout
    assert "Signing: blocked" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Order cancellation: blocked" in completed.stdout
    assert "### L2 credentials/auth" in diagnosis
    assert "### selected-token payload readiness" in diagnosis
    assert RAW_PRIVATE_KEY not in completed.stdout
    assert RAW_SECRET not in completed.stdout
    assert RAW_PRIVATE_KEY not in diagnosis
    assert RAW_SECRET not in diagnosis


def test_cli_requires_dry_run_and_rejects_forbidden_runtime_flags(tmp_path: Path) -> None:
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.real_local_check_evidence_review",
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
            "pm_bot.operator_runner.real_local_check_evidence_review",
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


def test_no_submit_cancel_sign_network_env_or_browser_runtime_calls_exist() -> None:
    source = "\n".join(
        [
            inspect.getsource(review_module),
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
