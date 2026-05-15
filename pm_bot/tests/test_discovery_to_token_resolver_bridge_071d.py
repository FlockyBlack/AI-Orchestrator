from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.discovery_to_token_resolver_bridge import (
    discovery_to_token_resolver_bridge_artifact_paths,
    run_discovery_to_token_resolver_bridge,
)
import pm_bot.trading_core.discovery_to_token_resolver_bridge as bridge_module
import pm_bot.trading_core.discovery_to_token_resolver_bridge_models as models_module
from pm_bot.trading_core.discovery_to_token_resolver_bridge_models import (
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_NO_DISCOVERY,
    STATUS_BLOCKED_NO_SOURCE_TOKEN,
    STATUS_READY,
    STATUS_SELECTION_REQUIRED,
    validate_discovery_to_token_resolver_bridge_result,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"

RUNTIME_FILES = (
    Path("pm_bot/trading_core/discovery_to_token_resolver_bridge_models.py"),
    Path("pm_bot/trading_core/discovery_to_token_resolver_bridge.py"),
    Path("pm_bot/operator_runner/discovery_to_token_resolver_bridge.py"),
)

REQUIRED_ARTIFACT_NAMES = {
    "discovery_to_token_resolver_bridge_071d_result.json",
    "latest_discovery_to_token_resolver_bridge_status_071d.json",
    "discovery_to_token_candidate_contract_071d.json",
    "discovery_to_token_operator_selection_required_071d.json",
    "discovery_to_token_resolver_bridge_safety_snapshot_071d.json",
    "discovery_to_token_resolver_bridge_operator_summary_071d.md",
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


def _discovery_payload(token_ids: list[str] | None = None, *, source_backed: bool = True) -> dict[str, Any]:
    token_values = token_ids if token_ids is not None else ["1001"]
    return {
        "contract_version": "pmbot_public_market_token_discovery_result_071a.v1",
        "task_id": "ORCH-PMBOT-TRADING-MVP-071A-PUBLIC-MARKET-TOKEN-DISCOVERY-NO-TRADING",
        "status": "source_backed_candidates_ready",
        "market": "BTC",
        "strategy": "tiny-momentum",
        "market_candidate_count": 1,
        "outcome_token_candidate_count": len(token_values),
        "market_candidates": [
            {
                "market_candidate_id": "market-candidate-071a",
                "market_id": "0x" + ("a" * 64),
                "market_slug": "bitcoin-up-or-down-may-15-2026",
                "question": "Will Bitcoin be above the public threshold?",
                "source_name": "public_gamma_live_read_only",
                "source_type": "public_gamma_read_only",
                "source_origin": "public_network",
                "source_path": "/events",
                "source_backed": True,
                "source_payload_hash": "hash-071a",
            }
        ],
        "outcome_token_candidates": [
            {
                "token_candidate_id": f"token-candidate-071a-{index}",
                "market_candidate_id": "market-candidate-071a",
                "market_id": "0x" + ("a" * 64),
                "market_slug": "bitcoin-up-or-down-may-15-2026",
                "question": "Will Bitcoin be above the public threshold?",
                "outcome_name": "Yes" if index == 0 else "No",
                "outcome_index": index,
                "token_id": token_id,
                "source_field": "clobTokenIds",
                "source_name": "public_gamma_live_read_only",
                "source_type": "public_gamma_read_only",
                "source_origin": "public_network",
                "source_path": "/events",
                "source_backed": source_backed,
                "token_id_is_source_backed": source_backed,
                "token_id_is_generated": False,
                "source_payload_hash": "hash-071a",
            }
            for index, token_id in enumerate(token_values)
        ],
        "generated_at": GENERATED_AT,
        "dry_run": True,
        "allowed_for_live": False,
    }


def _write_discovery(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


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


def test_single_source_backed_candidate_produces_070b_candidate_contract_without_trading(tmp_path: Path) -> None:
    discovery_path = _write_discovery(tmp_path / "071a" / "public_market_token_discovery_071a_result.json", _discovery_payload(["1001"]))

    result = run_discovery_to_token_resolver_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        discovery_result_path=discovery_path,
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    target = result["target_contract"]

    assert result["status"] == STATUS_READY
    assert result["source_backed_candidate_count"] == 1
    assert result["valid_source_backed_candidate_count"] == 1
    assert target["target_resolver"] == "first_order_market_token_resolver_070b"
    assert target["market_slug"] == "bitcoin-up-or-down-may-15-2026"
    assert target["condition_id"] == "0x" + ("a" * 64)
    assert target["token_id"] == "1001"
    assert target["outcome_token_id"] == "1001"
    assert target["outcome_name"] == "Yes"
    assert target["token_id_source_backed"] is True
    assert target["token_id_generated"] is False
    assert target["fake_token_id_generated"] is False
    assert target["target_contract_executable"] is False
    assert result["operator_selection_required"]["selection_required"] is False
    assert validate_discovery_to_token_resolver_bridge_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_multiple_candidates_require_operator_selection_and_do_not_auto_pick(tmp_path: Path) -> None:
    discovery_path = _write_discovery(tmp_path / "071a" / "public_market_token_discovery_071a_result.json", _discovery_payload(["1001", "1002"]))

    result = run_discovery_to_token_resolver_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        discovery_result_path=discovery_path,
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    target = result["target_contract"]

    assert result["status"] == STATUS_SELECTION_REQUIRED
    assert result["valid_source_backed_candidate_count"] == 2
    assert target["token_id"] == ""
    assert target["token_id_source"] == "blocked_no_selected_source_backed_token_id"
    assert target["operator_selection_required"] is True
    assert result["operator_selection_required"]["selection_required"] is True
    assert result["operator_selection_required"]["candidate_count"] == 2
    assert result["operator_selection_required"]["auto_pick_for_live"] is False
    assert validate_discovery_to_token_resolver_bridge_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_operator_selection_can_choose_source_backed_candidate_for_review_only_contract(tmp_path: Path) -> None:
    discovery_path = _write_discovery(tmp_path / "071a" / "public_market_token_discovery_071a_result.json", _discovery_payload(["1001", "1002"]))

    result = run_discovery_to_token_resolver_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        discovery_result_path=discovery_path,
        selected_candidate_id="token-candidate-071a-1",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    target = result["target_contract"]

    assert result["status"] == STATUS_READY
    assert target["token_id"] == "1002"
    assert target["outcome_name"] == "No"
    assert target["operator_selection_used"] is True
    assert result["operator_selection_required"]["selection_required"] is False
    assert validate_discovery_to_token_resolver_bridge_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_no_source_backed_token_id_blocks_without_fake_id(tmp_path: Path) -> None:
    discovery_path = _write_discovery(
        tmp_path / "071a" / "public_market_token_discovery_071a_result.json",
        _discovery_payload(["1001"], source_backed=False),
    )

    result = run_discovery_to_token_resolver_bridge(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        discovery_result_path=discovery_path,
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert result["status"] == STATUS_BLOCKED_NO_SOURCE_TOKEN
    assert result["target_contract"]["token_id"] == ""
    assert result["target_contract"]["token_id_generated"] is False
    assert result["target_contract"]["fake_token_id_generated"] is False
    assert "fake-token-id-071d" not in json.dumps(result)
    assert validate_discovery_to_token_resolver_bridge_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_runner_emits_required_artifacts_on_missing_discovery_path(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.discovery_to_token_resolver_bridge",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--discovery-artifacts-dir",
            str(tmp_path / "missing_071a"),
            "--artifacts-dir",
            str(tmp_path / "artifacts"),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = discovery_to_token_resolver_bridge_artifact_paths(tmp_path / "artifacts")
    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert "Discovery to token resolver bridge 071D completed." in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert set(p.name for p in (tmp_path / "artifacts").iterdir() if p.is_file()) == REQUIRED_ARTIFACT_NAMES
    assert result["status"] == STATUS_BLOCKED_NO_DISCOVERY
    assert result["target_contract"]["token_id"] == ""
    assert result["latest_status"]["allowed_for_live"] is False
    assert validate_discovery_to_token_resolver_bridge_result(result)["valid"] is True
    _assert_required_false_flags(result)


def test_no_signing_order_auth_network_or_browser_runtime_calls_exist() -> None:
    source = (
        inspect.getsource(bridge_module)
        + "\n"
        + inspect.getsource(models_module)
        + "\n"
        + Path("pm_bot/operator_runner/discovery_to_token_resolver_bridge.py").read_text(encoding="utf-8")
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


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = ("while true", "time.sleep", "threading", "asyncio", "sched.")
    for path in RUNTIME_FILES:
        lowered = path.read_text(encoding="utf-8").lower()
        for term in forbidden_runtime_terms:
            assert re.search(re.escape(term), lowered) is None, path
