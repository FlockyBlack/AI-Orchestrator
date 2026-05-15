from __future__ import annotations

import inspect
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pm_bot.operator_runner.live_readonly_status_aggregator as runner_module
import pm_bot.trading_core.live_readonly_status_aggregator as aggregator_module
import pm_bot.trading_core.live_readonly_status_models as model_module
from pm_bot.trading_core.live_readonly_status_aggregator import (
    live_readonly_status_aggregator_artifact_paths,
    run_live_readonly_status_aggregator,
)
from pm_bot.trading_core.live_readonly_status_models import FORCED_FALSE_EXECUTION_FIELDS, STATUS_FIELDS

GENERATED_AT = "2026-05-15T00:00:00+04:00"

RAW_WALLET = "0x3006000000000000000000000000000000008989"
RAW_FUNDER = "0x1111000000000000000000000000000000005555"
RAW_SECRET = "raw-private-key-or-api-secret-071b-never-output"
RAW_BALANCE = "fake-balance-value-071b-never-output"
RAW_ALLOWANCE = "fake-allowance-value-071b-never-output"
RAW_ORDER_ID = "fake-order-id-071b-never-output"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_source_artifacts(root: Path) -> None:
    _write_json(
        root / "clob_l2_auth_readonly_probe_067c" / "latest_clob_l2_auth_readonly_probe_status_067c.json",
        {
            "contract_version": "pmbot_latest_clob_l2_auth_readonly_probe_status_067c.v1",
            "task_id": "ORCH-PMBOT-TRADING-MVP-067C-CLOB-L2-AUTH-READONLY-PROBE-NO-ORDERS",
            "status": "authenticated_readonly_probe_succeeded_live_blocked",
            "auth_verified": True,
            "open_order_count": 2,
            "balance_allowance_probe_status": "succeeded_redacted",
            "private_key": RAW_SECRET,
            "api_secret": RAW_SECRET,
            "raw_order_rows": [{"order_id": RAW_ORDER_ID}],
            "balance": RAW_BALANCE,
            "allowance": RAW_ALLOWANCE,
            "allowed_for_live": False,
            "private_key_read": False,
            "order_submission_attempted": False,
            "order_cancellation_attempted": False,
            "signing_attempted": False,
        },
    )
    _write_json(
        root / "live_account_readonly_state_probe_070c" / "latest_live_account_readonly_state_status_070c.json",
        {
            "contract_version": "pmbot_latest_live_account_readonly_state_status_070c.v1",
            "task_id": "ORCH-PMBOT-TRADING-MVP-070C-LIVE-ACCOUNT-READONLY-STATE-PROBE-NO-ORDERS",
            "status": "account_state_probe_succeeded_live_blocked",
            "open_orders_status": "succeeded",
            "open_order_count": 2,
            "balance_allowance_status": "succeeded_redacted",
            "balance_allowance_availability_status": "available_redacted:balance,allowance",
            "wallet_address_status": "present_redacted",
            "wallet_address_redacted": "0x3006...8989",
            "funder_address_status": "present_redacted",
            "funder_address_redacted": "0x1111...5555",
            "signature_type_status": "present_redacted",
            "signature_type_redacted": "3",
            "private_key": RAW_SECRET,
            "allowed_for_live": False,
            "private_key_read": False,
            "order_submission_attempted": False,
            "order_cancellation_attempted": False,
            "signing_attempted": False,
        },
    )
    _write_json(
        root / "telegram_wallet_auth_status_067e" / "latest_telegram_wallet_auth_status_067e.json",
        {
            "contract_version": "pmbot_telegram_wallet_auth_status_067e.v1",
            "task_id": "ORCH-PMBOT-TELEGRAM-067E-WALLET-AUTH-STATUS-DASHBOARD-NO-LIVE",
            "status": "telegram_wallet_auth_status_ready_review_only",
            "l2_auth_probe_status": "ok",
            "open_orders_status": "known_from_dashboard",
            "balance_allowance_status": "known_from_dashboard",
            "wallet_display": RAW_WALLET,
            "funder_display": RAW_FUNDER,
            "signature_type_display": "3",
            "private_key": RAW_SECRET,
            "allowed_for_live": False,
            "private_key_read": False,
        },
    )


def _all_false_safety_flags(value: Mapping[str, Any]) -> None:
    rendered = json.dumps(value, sort_keys=True)
    assert value["allowed_for_live"] is False
    assert value["private_key_read"] is False
    assert value["network_access_performed"] is False
    assert value["order_submission_attempted"] is False
    assert value["order_cancellation_attempted"] is False
    assert value["signing_attempted"] is False
    assert value["resolved_blocker_count"] == 0
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if field == "resolved_blocker_count":
            assert f'"{field}": 0' in rendered
        else:
            assert f'"{field}": false' in rendered, field


def test_missing_artifacts_produce_unknown_not_fake_statuses(tmp_path: Path) -> None:
    result = run_live_readonly_status_aggregator(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "missing_sources",
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    latest = result["latest_status"]

    assert latest["source_available_count"] == 0
    for field in STATUS_FIELDS:
        assert latest[field] == "unknown", field
        assert latest["fields"][field]["source_id"] == "none"
    assert latest["unknown_status_count"] == len(STATUS_FIELDS)
    assert result["no_fake_data"] is True
    assert result["no_fake_balances_pnl_orders"] is True
    _all_false_safety_flags(result)


def test_aggregates_local_067c_070c_and_067e_statuses_without_raw_values(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    _write_source_artifacts(artifact_root)

    result = run_live_readonly_status_aggregator(
        market="btc",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=artifact_root,
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    latest = result["latest_status"]
    rendered = json.dumps(result, sort_keys=True)

    assert latest["market"] == "BTC"
    assert latest["l2_auth_status"] == "authenticated_readonly_probe_succeeded_live_blocked"
    assert latest["open_orders_status"] == "succeeded"
    assert latest["balance_status"] == "available_redacted"
    assert latest["allowance_status"] == "available_redacted"
    assert latest["wallet_address_status"] == "present_redacted"
    assert latest["funder_status"] == "present_redacted"
    assert latest["signature_type_status"] == "present_redacted"
    assert latest["fields"]["open_orders_status"]["source_id"] == "live_account_readonly_state_probe_070c"
    assert latest["fields"]["l2_auth_status"]["source_id"] == "clob_l2_auth_readonly_probe_067c"
    for raw in (RAW_WALLET, RAW_FUNDER, RAW_SECRET, RAW_BALANCE, RAW_ALLOWANCE, RAW_ORDER_ID):
        assert raw not in rendered
    assert "open_order_count" not in rendered
    assert "order_id" not in rendered
    assert "realized_pnl" not in rendered
    assert "unrealized_pnl" not in rendered
    assert result["validation"]["valid"] is True
    _all_false_safety_flags(result)


def test_reads_only_fixed_local_artifact_paths(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    artifact_root = tmp_path / "artifacts"
    _write_source_artifacts(artifact_root)
    original_load_json_object = aggregator_module.load_json_object
    reads: list[Path] = []

    def guarded_load_json_object(path: str | Path, *, label: str = "input") -> dict[str, Any]:
        path_obj = Path(path).resolve()
        assert path_obj.is_relative_to(artifact_root.resolve())
        reads.append(path_obj)
        return original_load_json_object(path, label=label)

    monkeypatch.setattr(aggregator_module, "load_json_object", guarded_load_json_object)
    run_live_readonly_status_aggregator(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=artifact_root,
        artifact_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )

    assert {path.name for path in reads} == {
        "latest_clob_l2_auth_readonly_probe_status_067c.json",
        "latest_live_account_readonly_state_status_070c.json",
        "latest_telegram_wallet_auth_status_067e.json",
    }


def test_no_env_secret_network_submit_cancel_or_signing_call_paths_in_source() -> None:
    source = "\n".join(
        [
            inspect.getsource(aggregator_module),
            inspect.getsource(model_module),
            inspect.getsource(runner_module),
        ]
    ).lower()
    forbidden_terms = (
        "import os",
        "os.environ",
        "getenv(",
        "load_dotenv",
        "requests.",
        "httpx.",
        "urllib.request",
        "socket.",
        "websocket",
        "account.from_key",
        "eth_account",
        "web3",
    )
    for term in forbidden_terms:
        assert term not in source, term
    forbidden_call_patterns = (
        r"\bcreate_order\s*\(",
        r"\bpost_order\s*\(",
        r"\bsubmit_order\s*\(",
        r"\bplace_order\s*\(",
        r"\bsend_order\s*\(",
        r"\bcancel_order\s*\(",
        r"\bcancel_all\s*\(",
        r"\bsign_order\s*\(",
        r"\bsign_payload\s*\(",
        r"\bsign\s*\(",
        r"\bconnect_wallet\s*\(",
        r"\.post\s*\(",
        r"\.put\s*\(",
        r"\.patch\s*\(",
        r"\.delete\s*\(",
    )
    for pattern in forbidden_call_patterns:
        assert re.search(pattern, source) is None, pattern


def test_runner_emits_required_artifacts(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    out_dir = tmp_path / "runner_out"
    _write_source_artifacts(artifact_root)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.live_readonly_status_aggregator",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifact-root",
            str(artifact_root),
            "--artifacts-dir",
            str(out_dir),
        ],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = live_readonly_status_aggregator_artifact_paths(out_dir)

    assert completed.returncode == 0, completed.stderr
    assert "Live read-only status aggregation completed." in completed.stdout
    assert "Local artifacts only: true" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Private key read: false" in completed.stdout
    assert "Network calls: false" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert paths["result"].exists()
    assert paths["latest_status"].exists()
    assert paths["sources"].exists()
    assert paths["safety_snapshot"].exists()
    assert paths["operator_md"].exists()
    latest = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    assert latest["allowed_for_live"] is False
    assert latest["l2_auth_status"] == "authenticated_readonly_probe_succeeded_live_blocked"
